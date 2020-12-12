from exceptions import RtnException
from type_system import TypedValue, TypedSym, TypedStr, Void, op_res, op_res_type, op_cpp_repr, type_cpp_repr, check_assign_okay

def _indent(strlist):
    for i in range(len(strlist)):
        strlist[i] = '\t' + strlist[i]
    return strlist



class Func:
    def __init__(self, typed_sym, args, instrs, pos):
        assert isinstance(typed_sym, TypedSym)
        self._typed_sym = typed_sym
        self._args = args
        self._instrs = instrs
        self.pos = pos

    def run(self, vm):
        vm.run_ctx.push_func_scope(TypedValue(self, self._typed_sym.type))
        for arg in reversed(self._args):
            vm.run_ctx.init_symbol(arg, vm.run_pop(), self)
        try:
            vm.run(self._instrs)
        except RtnException as e:
            pass
        vm.run_ctx.pop_scope()

    def compile(self, vm):
        vm.comp_ctx.push_func_scope(TypedValue(self, self._typed_sym.type))
        for arg in self._args:
            vm.comp_ctx.declare_symbol(arg, self)
        blk_code = vm.compile(self._instrs)
        argList = ', '.join(('{} {}'.format(a.type_repr, a.string) for a in self._args))
        code = ['{} {}({}){{'.format(self._typed_sym.type_repr, self._typed_sym.sym, argList)]
        code += _indent(blk_code)
        code += ['}']
        vm.comp_ctx.pop_scope()
        # vm.comp_ctx
        return code


class Instrn:
    def __init__(self, pos):
        self.pos = pos

    def run(self, vm):
        raise NotImplementedError()

    def compile(self, vm):
        raise NotImplementedError()

    def __repr__(self):
        s = self.__class__.__name__ + ' '
        for k,v in vars(self).items():
            s += '{} {},'.format(k,v)
        return '(' + s[:-1] + ')'


class BinOp(Instrn):
    def __init__(self, op, pos):
        super().__init__(pos)
        self.op = op

    def run(self, vm):
        right = vm.run_pop()
        left = vm.run_pop()
        vm.run_push(op_res(self.op, left, right, self))

    def compile(self, vm):
        right = vm.comp_pop()
        left = vm.comp_pop()
        res_type = op_res_type(self.op, left.type, right.type, self)
        op_repr = op_cpp_repr(self.op)
        return vm.comp_push(
            TypedStr(
                '{} {} {}'.format(left.string, op_repr, right.string),
                res_type
            )
        )



class UnaryOp(Instrn):
    def __init__(self, op, pos):
        super().__init__(pos)
        self.op = op

    def run(self, vm):
        operand = vm.run_pop()
        vm.run_push(op_res(self.op, operand, self))

    def compile(self, vm):
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

    def run(self, vm):
        typed_value = vm.run_pop()
        vm.run_ctx.assign_symbol(self._sym, typed_value, self)

    def compile(self, vm):
        typed_str = vm.comp_pop()
        vm.comp_ctx.check_assign_okay(self._sym, typed_str, self.pos)
        return '{} = {};'.format(self._sym, typed_str.string)

class Decl(Instrn):
    def __init__(self, typed_sym, pos):
        super().__init__(pos)
        assert isinstance(typed_sym, TypedSym)
        self._typed_sym = typed_sym

    def run(self, vm):
        vm.run_ctx.declare_symbol(self._typed_sym, self)

    def compile(self, vm):
        vm.comp_ctx.declare_symbol(self._typed_sym, self)
        type_repr = type_cpp_repr(self._typed_sym.type)
        return '{} {};'.format(type_repr, self._typed_sym.sym)


class Pushi(Instrn):
    def __init__(self, value, pos):
        super().__init__(pos)
        assert isinstance(value, TypedValue)
        self._value = value

    def run(self, vm):
        vm.run_push(self._value)

    def compile(self, vm):
        code = vm.comp_pushi(self._value)
        return code


class Push(Instrn):
    def __init__(self, sym, pos):
        super().__init__(pos)
        self._sym = sym

    def run(self, vm):
        vm.run_push(vm.run_ctx.read_symbol(self._sym, self))

    def compile(self, vm):
        return vm.comp_push_sym(self._sym, self)


class Call(Instrn):
    def __init__(self, sym, argExprns, pos):
        super().__init__(pos)
        self._sym = sym
        self._argExprns = argExprns

    def run(self, vm):
        for instrs in self._argExprns:
            vm.run(instrs)
        vm.call(self._sym, self)

    def compile(self, vm):
        call_code = ''
        prep_code = []
        for argExprn in self._argExprns:
            prep_code += vm.compile(argExprn)
            call_code += (', '  if call_code else '') + vm.comp_pop().string
        call_code = '{}({})'.format(self._sym, call_code)
        vm.comp_push_fragment( self._sym, call_code, self )
        return prep_code

class Rtn(Instrn):
    def __init__(self, exprn, pos):
        super().__init__(pos)
        self._exprn = exprn

    def run(self, vm):
        if self._exprn:
            vm.run(self._exprn)
        else:
            vm.run_push(TypedValue(None, Void()))
        check_assign_okay(vm.run_ctx.func.type, vm.run_peek().type, self.pos)
        raise RtnException()

    def compile(self, vm):
        rtn_val = TypedValue(None, Void())
        if self._exprn:
            code = vm.compile(self._exprn)
            rtn_val = vm.comp_pop()
        check_assign_okay(vm.comp_ctx.func.type, rtn_val.type, self)
        return 'return {};'.format(rtn_val.string if self._exprn else '')

class Pop(Instrn):
    def run(self, vm):
        vm.run_pop()

    def compile(self, vm):
        vm.comp_pop()
        return ''


class IfElse(Instrn):
    def __init__(self, condInstr, ifBlockInstr, elseBlockInstr, pos):
        super().__init__(pos)
        self._condInstr = condInstr
        self._ifBlockInstr = ifBlockInstr
        self._elseBlockInstr = elseBlockInstr


    def run(self, vm):
        vm.run(self._condInstr)
        cond = vm.run_pop().value
        with vm.run_ctx.raii_push_scope():
            if cond:
                vm.run(self._ifBlockInstr)
            else:
                vm.run(self._elseBlockInstr)

    def compile(self, vm):
        code = vm.compile(self._condInstr)
        # vm.comp_ctx.push_scope()
        with vm.comp_ctx.raii_push_scope():
            code += ['if(' + vm.comp_pop().string + '){']
            code += _indent(vm.compile(self._ifBlockInstr))
            elseBlk = _indent(vm.compile(self._elseBlockInstr))
            if elseBlk:
                code += ['} else {']
                code += elseBlk
            code += ['}']
        # vm.comp_ctx.pop_scope()
        return code

class WhileLoop(Instrn):
    def __init__(self, condInstrs, loopInstrs, pos):
        super().__init__(pos)
        self._condInstrs = condInstrs
        self._loopInstrs = loopInstrs


    def run(self, vm):
        while True:
            vm.run(self._condInstrs)
            cond = vm.run_pop()
            if not cond.value:
                break
            with vm.run_ctx.raii_push_scope():
                vm.run(self._loopInstrs)

    def compile(self, vm):
        code = []

        code += ['while(1){']
        blockCode = vm.compile(self._condInstrs)
        blockCode += ['if(!(' + str(vm.comp_pop().string) +')){']
        blockCode += _indent(['break;'])
        blockCode += ['}']
        with vm.comp_ctx.raii_push_scope():
            blockCode += vm.compile(self._loopInstrs)
        code += _indent(blockCode)
        code += ['}']

        return code



