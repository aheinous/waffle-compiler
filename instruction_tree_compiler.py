from exceptions import MixinException, ReadUninitializedValue
from type_system import Void
from typed_data import TFrag
from context import TYPE, VALUE
from instruction_tree_visitor import InstrnTreePrinter, InstrnTreeVisitor

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
        self._tmp_counters = {}

    def _next_tmp(self):
        scope_uid = self.ctx.cur_scope_uid()
        if scope_uid not in self._tmp_counters:
            self._tmp_counters[scope_uid] = -1
        self._tmp_counters[scope_uid] += 1
        return self._tmp_counters[scope_uid]

    def _add_code(self, code):
        if isinstance(code, str):
            code = [code]
        self._code += _indent(code, self._num_indents)


    def compile_tree(self, instrn_blk):
        self._add_code('#include <iostream>')
        self._add_code('#include <string>')
        self.visit_blk(instrn_blk)
        code = self._code
        self._code = []
        return code

    def visit_Assign(self, assign):
        right = self.vm.comp_pop()
        left = self.vm.comp_pop()
        left.checkAssignOkay(right, assign.pos)
        self._add_code( '{} = {};'.format(left.repr, right.repr))

    def visit_Decl(self, decl):
        tsym = decl.typed_sym
        self.ctx.declare_symbol(tsym, decl.pos)
        self._add_code( '{} {};'.format(tsym.type_repr, tsym.sym))

    def visit_Push(self, push):
        type_ = self.ctx.read(push.sym, TYPE, push.pos)
        typed_str = TFrag(push.sym, type_)

        self.vm.comp_push(typed_str)


    def visit_Pushi(self, pushi):
        self.vm.comp_push(pushi.value.tfrag())


    def visit_Pop(self, pop):
        self.vm.comp_pop()


    def visit_BinOp(self, binop):
        right = self.vm.comp_pop()
        left = self.vm.comp_pop()
        # res_type = op_res_type(binop.op, left.type, right.type, binop.pos)
        res_type = left.opResType(binop.op, right, binop.pos)

        tmp_name = 'tmp_{}'.format(self._next_tmp())
        self.vm.comp_push(TFrag(tmp_name, res_type))

        code = '{} {} = {} {} {};'.format(  res_type.repr,
                                            tmp_name,
                                            left.repr,
                                            binop.op.repr,
                                            right.repr)
        self._add_code( code)



    def visit_UnaryOp(self, unaryop):
        operand = self.vm.comp_pop()
        res = operand.unaryOpRes(unaryop.op, self.ctx, unaryop.pos)
        self.vm.comp_push(res)


    def visit_IfElse(self, ifelse):
        self.visit_blk(ifelse.condBlk)

        condition = self.vm.comp_pop()
        self._add_code('if(' + condition.repr + '){')

        with self.ctx.enter_scope(ifelse.ifBlk.uid):
            self._num_indents += 1
            self.visit_blk(ifelse.ifBlk)
            self._num_indents -= 1

        if ifelse.elseBlk:
            self._add_code('} else {')
            with self.ctx.enter_scope(ifelse.elseBlk.uid):
                self._num_indents += 1
                self.visit_blk(ifelse.elseBlk)
                self._num_indents -= 1

        self._add_code('}')



    def visit_WhileLoop(self, whileloop):

        self._add_code('while(1){')
        self._num_indents += 1
        self.visit_blk(whileloop.condBlk)
        self._add_code('if(!(' + str(self.vm.comp_pop().repr) +')){')
        self._add_code(_indent(['break;'], 1))
        self._add_code('}')
        with self.ctx.enter_scope(whileloop.loop.uid):
            self.visit_blk(whileloop.loop)
        self._num_indents -= 1
        self._add_code('}')



    def visit_InitFunc(self, init_func):
        self.ctx.init_symbol(init_func.typed_sym, init_func.typed_func, init_func.pos)

        func = init_func.typed_func.value(self.ctx, init_func.pos)
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
            self.visit_blk(func.instrns)
            self._num_indents -= 1
            self._add_code('}')




    def visit_Call(self, call):
        arg_code = ''
        for arg_exprn in call.arg_exprns:
            self.visit_blk(arg_exprn)
            arg_code += (', '  if arg_code else '') + self.vm.comp_pop().repr

        call_code = '{}({})'.format(call.func_sym, arg_code)
        type_ = self.ctx.read(call.func_sym, TYPE, call.pos)
        self.vm.comp_push(TFrag(call_code, type_))


    def visit_Rtn(self, rtn):
        rtnVal = TFrag('', Void())
        if rtn.exprn:
            self.visit_blk(rtn.exprn)
            rtnVal = self.vm.comp_pop()
        self.call_stack.checkRtnTypeOkay(rtnVal, rtn.pos)
        self._add_code( 'return {};'.format(rtnVal.repr))

    def visit_Mixin(self, mixin):
        self.compiler.run_exprn_tree(mixin.exprn, mixin.pos)
        code = self.vm.run_pop()
        try:
            value = code.value(self.ctx, mixin.pos)
        except ReadUninitializedValue as e:
            raise MixinException(e.sym, e.pos)
        sub_tree = self.compiler.compile_exprn_code(value, mixin.pos)
        self.visit_blk(sub_tree)

    def visit_MixinStatements(self, mixin):
        self.compiler.run_exprn_tree(mixin.statements, mixin.pos)
        s = self.vm.run_pop()
        s = s.value(self.ctx, mixin.pos)
        sub_tree = self.compiler.compile_statements(s, mixin.pos)
        InstrnTreePrinter().start(sub_tree)
        self.visit_blk(sub_tree)


    def visit_PLocal(self, plocal):
        inner_tbl = self.ctx.cur_scope.symbol_tbl._tbl
        syms = sorted(inner_tbl.keys())
        self._add_code('std::cout << "vvvvv PLocal vvvvv" << std::endl;')
        for sym in syms:
            type_ = self.ctx.read(sym, TYPE, plocal.pos)
            self._add_code('std::cout << "{} ; " << {} << " ; {}" << std::endl;'.format(sym, sym, type_.repr))
        self._add_code('std::cout << "^^^^^ PLocal ^^^^^" << std::endl;')
