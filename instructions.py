from call_stack import CallStack
from context import TYPE, VALUE
from exceptions import RtnException
from type_system import TypedValue, TypedSym, TypedStr, Void, op_res, op_res_type, op_cpp_repr, type_cpp_repr, check_assign_okay

def _indent(strlist):
    for i in range(len(strlist)):
        strlist[i] = '\t' + strlist[i]
    return strlist



call_stack = CallStack()




class Func:
    def __init__(self, typed_sym, args, instrns, pos):
        assert isinstance(typed_sym, TypedSym)
        self._typed_sym = typed_sym
        self._args = args
        self.instrns = instrns
        self.pos = pos

    @property
    def rtn_type(self):
        return self._typed_sym.type

    def run(self, vm, ctx):
        # ctx.push_func_scope(TypedValue(self, self._typed_sym.type))
        with call_stack.push(self), ctx.enter_scope(self.instrns.uid):
            for arg in reversed(self._args):
                ctx.init_symbol(arg, vm.run_pop(), self.pos)
            try:
                self.instrns.run( vm, ctx)
            except RtnException as e:
                pass
        # ctx.pop_scope()

    def compile(self, vm, ctx):
        # ctx.push_func_scope(TypedValue(self, self._typed_sym.type))
        with call_stack.push(self), ctx.enter_scope(self.instrns.uid):
            for arg in self._args:
                ctx.declare_symbol(arg, self.pos)
            # blk_code = vm.compile(self._instr, ctx)
            blk_code = self.instrns.compile(vm, ctx)
            argList = ', '.join(('{} {}'.format(a.type_repr, a.string) for a in self._args))
            code = ['{} {}({}){{'.format(self._typed_sym.type_repr, self._typed_sym.sym, argList)]
            code += _indent(blk_code)
            code += ['}']
        # ctx.pop_scope()
        # ctx
        return code


class Instrn:
    def __init__(self, pos):
        self.pos = pos
        self._child_scopes = {}

    def _add_child_scope(self, name, child_scope):
        self._child_scopes[name] = child_scope

    @property
    def child_scopes(self):
        return self._child_scopes



    def run(self, vm, ctx):
        raise NotImplementedError()

    def compile(self, vm, ctx):
        raise NotImplementedError()

    def __repr__(self):
        s = self.__class__.__name__ + ' '
        # for k,v in vars(self).items():
        #     s += '{} {},'.format(k,v)
        return '(' + s + str(self.pos) + ')'


class BinOp(Instrn):
    def __init__(self, op, pos):
        super().__init__(pos)
        self.op = op

    def run(self, vm, ctx):
        right = vm.run_pop()
        left = vm.run_pop()
        vm.run_push(op_res(self.op, left, right, self))

    def compile(self, vm, ctx):
        right = vm.comp_pop()
        left = vm.comp_pop()
        res_type = op_res_type(self.op, left.type, right.type, self)

        tmp_name = 'tmp_{}'.format(ctx.next_tmp())
        vm.comp_push(TypedStr(tmp_name, res_type))

        code = '{} {} = {} {} {};'.format(  res_type.repr,
                                            tmp_name,
                                            left.string,
                                            self.op.repr,
                                            right.string)
        return code


class UnaryOp(Instrn):
    def __init__(self, op, pos):
        super().__init__(pos)
        self.op = op

    def run(self, vm, ctx):
        operand = vm.run_pop()
        vm.run_push(op_res(self.op, operand, self))

    def compile(self, vm, ctx):
        operand = vm.run_pop()
        res_type = op_res_type(self.op, operand, self)
        op_repr = op_cpp_repr(self.op)
        return vm.comp_push(
            TypedValue(
                '{} {}'.format(op_repr, operand.value),
                res_type
            )
        )

class Assign(Instrn):
    def __init__(self, sym, pos):
        super().__init__(pos)
        assert  isinstance(sym, str)
        self._sym = sym

    def run(self, vm, ctx):
        typed_value = vm.run_pop()
        ctx.assign_symbol(self._sym, typed_value, self)

    def compile(self, vm, ctx):
        typed_str = vm.comp_pop()
        ctx.check_assign_okay(self._sym, typed_str, self.pos)
        return '{} = {};'.format(self._sym, typed_str.string)

class Decl(Instrn):
    def __init__(self, typed_sym, pos):
        super().__init__(pos)
        assert isinstance(typed_sym, TypedSym)
        self._typed_sym = typed_sym

    def run(self, vm, ctx):
        ctx.declare_symbol(self._typed_sym, self)

    def compile(self, vm, ctx):
        ctx.declare_symbol(self._typed_sym, self)
        type_repr = type_cpp_repr(self._typed_sym.type)
        return '{} {};'.format(type_repr, self._typed_sym.sym)


class Pushi(Instrn):
    def __init__(self, value, pos):
        super().__init__(pos)
        assert isinstance(value, TypedValue)
        self._value = value

    def run(self, vm, ctx):
        vm.run_push(self._value)

    def compile(self, vm, ctx):
        vm.comp_push(self._value.cpp_repr)
        return []


class Push(Instrn):
    def __init__(self, sym, pos):
        super().__init__(pos)
        self._sym = sym

    def run(self, vm, ctx):
        vm.run_push(ctx.read(self._sym, VALUE, self.pos))

    def compile(self, vm, ctx):

        type_ = ctx.read(self._sym, TYPE, self.pos)
        typed_str = TypedStr(self._sym, type_)

        vm.comp_push(typed_str)
        return []


class InitFunc(Instrn):
    def __init__(self, typed_sym, typed_func, pos):
        super().__init__(pos)
        self._typed_sym = typed_sym
        self._typed_func = typed_func
        self._add_child_scope('func_blk', typed_func.value.instrns)

    def run(self, vm, ctx):
        ctx.init_symbol(self._typed_sym, self._typed_func, self.pos)

    def compile(self, vm, ctx):
        ctx.init_symbol(self._typed_sym, self._typed_func, self.pos)
        return self._typed_func.value.compile(vm, ctx)




class Call(Instrn):
    def __init__(self, func_sym, argExprns, pos):
        super().__init__(pos)
        self._func_sym = func_sym
        self._argExprns = argExprns

    def run(self, vm, ctx):
        for instrns in self._argExprns:
            # vm.run(instrns, ctx)
            instrns.run(vm, ctx)

        # vm.call(self._func_sym, self)
        t_func = ctx.read(self._func_sym, VALUE, self.pos)
        t_func.value.run(vm, ctx)


    def compile(self, vm, ctx):
        arg_code = ''
        prep_code = []
        for argExprn in self._argExprns:
            # prep_code += vm.compile(argExprn, ctx)
            prep_code += argExprn.compile(vm, ctx)
            arg_code += (', '  if arg_code else '') + vm.comp_pop().string

        call_code = '{}({})'.format(self._func_sym, arg_code)
        type_ = ctx.read(self._func_sym, TYPE, self.pos)
        vm.comp_push(TypedStr(call_code, type_))
        return prep_code

class Rtn(Instrn):
    def __init__(self, exprn, pos):
        super().__init__(pos)
        self._exprn = exprn

    def run(self, vm, ctx):
        if self._exprn:
            self._exprn.run(vm, ctx)
        else:
            vm.run_push(TypedValue(None, Void()))
        # TODO Check assign
        check_assign_okay(call_stack.peek().rtn_type, vm.run_peek().type, self.pos)
        raise RtnException()

    def compile(self, vm, ctx):
        rtn_val = TypedValue(None, Void())
        if self._exprn:
            # code = vm.compile(self._exprn, ctx)
            code = self._exprn.compile(vm, ctx)
            rtn_val = vm.comp_pop()
        # TODO Check assign
        # check_assign_okay(ctx.func.type, rtn_val.type, self)
        check_assign_okay(call_stack.peek().rtn_type, rtn_val.type, self.pos)
        return 'return {};'.format(rtn_val.string if self._exprn else '')

class Pop(Instrn):
    def run(self, vm, ctx):
        vm.run_pop()

    def compile(self, vm, ctx):
        vm.comp_pop()
        return ''


class IfElse(Instrn):
    def __init__(self, condBlk, ifBlk, elseBlk, pos):
        super().__init__(pos)
        # ifBlk.uid
        # elseBlk.uid
        self._condBlk = condBlk
        self._add_child_scope('if_blk', ifBlk)
        self._add_child_scope('else_blk', elseBlk)

        self._ifBlk = ifBlk
        self._elseBlk = elseBlk


    def run(self, vm, ctx):
        # vm.run(self._condBlk, ctx)
        self._condBlk.run(vm, ctx)
        cond = vm.run_pop().value
        # with ctx.raii_push_scope():
        if cond:
            with ctx.enter_scope(self._ifBlk.uid):
                # vm.run(self._ifBlk, ctx)
                self._ifBlk.run(vm,ctx)
        else:
            with ctx.enter_scope(self._elseBlk.uid):
                # vm.run(self._elseBlk, ctx)
                self._elseBlk.run(vm, ctx)

    def compile(self, vm, ctx):
        # code = vm.compile(self._condBlk, ctx)
        code = self._condBlk.compile(vm, ctx)

        cond = vm.comp_pop()
        code += ['if(' + cond.string + '){']

        with ctx.enter_scope(self._ifBlk.uid):
            # code += _indent(vm.compile(self._ifBlk, ctx))
            code += _indent(self._ifBlk.compile(vm, ctx))

        if self._elseBlk:
            code += ['} else {']
            with ctx.enter_scope(self._elseBlk.uid):
                # code += _indent(vm.compile(self._elseBlk, ctx))
                code += _indent(self._elseBlk.compile(vm, ctx))

        code += ['}']
        return code

class WhileLoop(Instrn):
    def __init__(self, condBlk, loop, pos):
        super().__init__(pos)
        self._condBlk = condBlk
        self._loop = loop

        self._add_child_scope('loop', loop)

    def run(self, vm, ctx):
        while True:
            # vm.run(self._condBlk, ctx)
            self._condBlk.run(vm, ctx)
            cond = vm.run_pop()
            if not cond.value:
                break
            with ctx.enter_scope(self._loop.uid):
                # vm.run(self._loop, ctx)
                self._loop.run(vm, ctx)

    def compile(self, vm, ctx):
        code = []

        code += ['while(1){']
        # blockCode = vm.compile(self._condBlk, ctx)
        blockCode = self._condBlk.compile(vm, ctx)
        blockCode += ['if(!(' + str(vm.comp_pop().string) +')){']
        blockCode += _indent(['break;'])
        blockCode += ['}']
        # with ctx.raii_push_scope():
        with ctx.enter_scope(self._loop.uid):
            # blockCode += vm.compile(self._loop, ctx)
            blockCode += self._loop.compile(vm, ctx)
        code += _indent(blockCode)
        code += ['}']

        return code



