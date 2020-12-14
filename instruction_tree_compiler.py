from exceptions import RtnException
from type_system import TypedStr, TypedValue, Void, check_assign_okay, op_cpp_repr, op_res, op_res_type, type_cpp_repr
from context import TYPE, VALUE
from instruction_tree_visitor import InstrnTreeVisitor

def _indent(strlist, n):
    for i in range(len(strlist)):
        strlist[i] = n*'    ' + strlist[i]
    return strlist


class InstrnTreeCompiler(InstrnTreeVisitor):
    def __init__(self, vm, ctx, call_stack, compiler):
        super().__init__()
        self.vm = vm
        self.ctx = ctx
        self.call_stack = call_stack
        self.compiler = compiler
        self._code = []
        self._num_indents = 0


    def _add_code(self, code):
        if isinstance(code, str):
            code = [code]
        self._code += _indent(code, self._num_indents)


    def compile(self, instrn_blk):
        self.visit_blk(instrn_blk)
        code = self._code
        self._code = []
        return code

    def visit_Assign(self, assign):
        typed_str = self.vm.comp_pop()
        self.ctx.check_assign_okay(assign.sym, typed_str, assign.pos)
        self._add_code( '{} = {};'.format(assign.sym, typed_str.string))

    def visit_Decl(self, decl):
        self.ctx.declare_symbol(decl.typed_sym, decl)
        type_repr = type_cpp_repr(decl.typed_sym.type)
        self._add_code( '{} {};'.format(type_repr, decl.typed_sym.sym))

    def visit_Push(self, push):
        type_ = self.ctx.read(push.sym, TYPE, push.pos)
        typed_str = TypedStr(push.sym, type_)

        self.vm.comp_push(typed_str)


    def visit_Pushi(self, pushi):
        self.vm.comp_push(pushi.value.cpp_repr)


    def visit_Pop(self, pop):
        self.vm.comp_pop()


    def visit_BinOp(self, binop):
        right = self.vm.comp_pop()
        left = self.vm.comp_pop()
        res_type = op_res_type(binop.op, left.type, right.type, binop.pos)

        tmp_name = 'tmp_{}'.format(self.ctx.next_tmp())
        self.vm.comp_push(TypedStr(tmp_name, res_type))

        code = '{} {} = {} {} {};'.format(  res_type.repr,
                                            tmp_name,
                                            left.string,
                                            binop.op.repr,
                                            right.string)
        self._add_code( code)



    def visit_UnaryOp(self, unaryop):
        operand = self.vm.comp_pop()
        res_type = op_res_type(unaryop.op, operand.type, unaryop.pos)
        op_repr = op_cpp_repr(unaryop.op)
        self.vm.comp_push(
            TypedStr(
                '{}{}'.format(op_repr, operand.string),
                res_type
            )
        )


    def visit_IfElse(self, ifelse):
        self.compile(ifelse.condBlk)

        condition = self.vm.comp_pop()
        self._add_code('if(' + condition.string + '){')

        with self.ctx.enter_scope(ifelse.ifBlk.uid):
            self._num_indents += 1
            self.compile(ifelse.ifBlk)
            self._num_indents -= 1

        if ifelse.elseBlk:
            self._add_code('} else {')
            with self.ctx.enter_scope(ifelse.elseBlk.uid):
                self._num_indents += 1
                self.compile(ifelse.elseBlk)
                self._num_indents -= 1

        self._add_code('}')



    def visit_WhileLoop(self, whileloop):

        self._add_code('while(1){')
        self._num_indents += 1
        self.compile(whileloop.condBlk)
        self._add_code('if(!(' + str(self.vm.comp_pop().string) +')){')
        self._add_code(_indent(['break;'], 1))
        self._add_code('}')
        with self.ctx.enter_scope(whileloop.loop.uid):
            self.compile(whileloop.loop)
        self._num_indents -= 1
        self._add_code('}')



    def visit_InitFunc(self, init_func):
        self.ctx.init_symbol(init_func.typed_sym, init_func.typed_func, init_func.pos)

        func = init_func.typed_func.value
        with self.call_stack.push(func), self.ctx.enter_scope(func.instrns.uid):
            for arg in func.args:
                self.ctx.declare_symbol(arg, func.pos)

            arg_list = ', '.join(
                ('{} {}'.format(a.type_repr, a.string)
                for a in func.args)
                )
            self._add_code('{} {}({}){{'.format(func.typed_sym.type_repr,
                                                func.typed_sym.sym,
                                                arg_list))
            self._num_indents += 1
            self.compile(func.instrns)
            self._num_indents -= 1
            self._add_code('}')




    def visit_Call(self, call):
        arg_code = ''
        for arg_exprn in call.arg_exprns:
            self.compile(arg_exprn)
            arg_code += (', '  if arg_code else '') + self.vm.comp_pop().string

        call_code = '{}({})'.format(call.func_sym, arg_code)
        type_ = self.ctx.read(call.func_sym, TYPE, call.pos)
        self.vm.comp_push(TypedStr(call_code, type_))


    def visit_Rtn(self, rtn):
        rtn_val = TypedStr('', Void())
        if rtn.exprn:
            self.compile(rtn.exprn)
            rtn_val = self.vm.comp_pop()
        check_assign_okay(self.call_stack.peek().rtn_type, rtn_val.type, rtn.pos)
        self._add_code( 'return {};'.format(rtn_val.string))

    def visit_Mixin(self, mixin):
        self.compiler.run_exprn_tree(mixin.exprn)
        code = self.vm.run_pop()
        print('code:', code)
        # self._add_code(code.value)
        self.compiler.run_exprn_code(code.value, mixin.pos)
        value = self.vm.run_pop()
        print('value: ', value)
        self.vm.comp_push(value.cpp_repr)
