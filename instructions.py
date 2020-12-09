
from collections import namedtuple
from exceptions import RtnException, VMRuntimeException
from type_checking import *


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
        argList = ', '.join(('{} {}'.format(a.type, a.value) for a in self._args))
        code = ['{} {}({}){{'.format(self._typed_sym.type, self._typed_sym.value, argList)]
        code += _indent(blk_code)
        code += ['}']
        vm.comp_ctx.pop_scope()
        # vm.comp_ctx
        return code


class Instr:
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

class Add(Instr):
    def run(self, vm):
        right = vm.run_pop()
        left = vm.run_pop()
        vm.run_push(left.add(right, self))

    def compile(self, vm):
        right = vm.comp_pop()
        left = vm.comp_pop()
        return vm.comp_push(
            TypedValue(
                '{} + {}'.format(left.value, right.value),
                left.type # TODO proper type
            )
        )

class Sub(Instr):
    def run(self, vm):
        right = vm.run_pop()
        left = vm.run_pop()
        vm.run_push(left.sub(right, self))

    def compile(self, vm):
        right = vm.comp_pop()
        left = vm.comp_pop()
        return vm.comp_push(
            TypedValue(
                '{} - {}'.format(left.value, right.value),
                left.type # TODO proper type
            )
        )


class Mult(Instr):
    def run(self, vm):
        right = vm.run_pop()
        left = vm.run_pop()
        vm.run_push(left.mul(right, self))

    def compile(self, vm):
        right = vm.comp_pop()
        left = vm.comp_pop()
        return vm.comp_push(
            TypedValue(
                '{} * {}'.format(left.value, right.value),
                left.type # TODO proper type
            )
        )

class Div(Instr):
    def run(self, vm):
        right = vm.run_pop()
        left = vm.run_pop()

        vm.run_push(left.div(right, self))

    def compile(self, vm):
        right = vm.comp_pop()
        left = vm.comp_pop()
        return vm.comp_push(
            TypedValue(
                '{} / {}'.format(left.value, right.value),
                left.type # TODO proper type
            )
        )


class Neg(Instr):
    def run(self, vm):
        operand = vm.run_pop()
        vm.run_push(operand.neg(self))

    def compile(self, vm):
        operand = vm.comp_pop()
        return vm.comp_push('-{}'.format(operand))


class Assign(Instr):
    def __init__(self, sym, pos):
        super().__init__(pos)
        assert  isinstance(sym, str)
        self._sym = sym

    def run(self, vm):
        val = vm.run_pop()
        if val is Void:
            raise VMRuntimeException('Assigning a value of void', self.pos)
        vm.run_ctx.assign_symbol(self._sym, val, self)

    def compile(self, vm):
        val = vm.comp_pop()
        # print('assign ', val)
        if val is Void:
            raise VMRuntimeException('Assigning a value of void', self.pos)
        vm.comp_ctx.verify_assign(self._sym, val, self)
        return '{} = {};'.format(self._sym, val.value)

class Decl(Instr):
    def __init__(self, typed_sym, pos):
        super().__init__(pos)
        assert isinstance(typed_sym, TypedSym)
        self._typed_sym = typed_sym

    def run(self, vm):
        # vm.run_ctx.decl(self._typed_sym, TypedValue(0, self._typed_sym.type), self)
        vm.run_ctx.declare_symbol(self._typed_sym, self)

    def compile(self, vm):
        # vm.comp_ctx.decl(self._typed_sym, TypedValue(0, self._typed_sym.type), self)
        vm.comp_ctx.declare_symbol(self._typed_sym, self)
        return '{} {};'.format(self._typed_sym.type, self._typed_sym.name)


class Pushi(Instr):
    def __init__(self, value, pos):
        super().__init__(pos)
        assert isinstance(value, TypedValue)
        self._value = value

    def run(self, vm):
        vm.run_push(self._value)

    def compile(self, vm):
        code = vm.comp_pushi(self._value)
        return code


class Push(Instr):
    def __init__(self, sym, pos):
        super().__init__(pos)
        # assert isinstance(sym, TypedValue)
        self._sym = sym

    def run(self, vm):
        vm.run_push(vm.run_ctx.read_symbol(self._sym, self))

    def compile(self, vm):
        return vm.comp_push_sym(self._sym, self)


class Call(Instr):
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
            call_code += (', '  if call_code else '') + str(vm.comp_pop().value)
        call_code = '{}({})'.format(self._sym, call_code)
        vm.comp_push_fragment( self._sym, call_code, self )
        return prep_code

class Rtn(Instr):
    def __init__(self, exprn, pos):
        super().__init__(pos)
        self._exprn = exprn

    def run(self, vm):
        if self._exprn:
            vm.run(self._exprn)
        else:
            vm.run_push(Void)
        check_types_for_assign(vm.run_ctx.func, vm.run_peek(), self)
        raise RtnException()

    def compile(self, vm):
        rtn_val = TypedValue(Void, 'Void')
        if self._exprn:
            code = vm.compile(self._exprn)
            rtn_val = vm.comp_pop()
        check_types_for_assign(vm.comp_ctx.func, rtn_val, self)
        return 'return {};'.format(rtn_val.value if self._exprn else '')

class Pop(Instr):
    def run(self, vm):
        vm.run_pop()

    def compile(self, vm):
        vm.comp_pop()
        return ''


class IfElse(Instr):
    def __init__(self, condInstr, ifBlockInstr, elseBlockInstr, pos):
        super().__init__(pos)
        self._condInstr = condInstr
        self._ifBlockInstr = ifBlockInstr
        self._elseBlockInstr = elseBlockInstr


    def run(self, vm):
        vm.run(self._condInstr)
        cond = vm.run_pop().value
        if cond:
            vm.run(self._ifBlockInstr)
        else:
            vm.run(self._elseBlockInstr)

    def compile(self, vm):
        code = vm.compile(self._condInstr)
        code += ['if(' + str(vm.comp_pop().value) + '){']
        code += _indent(vm.compile(self._ifBlockInstr))
        elseBlk = _indent(vm.compile(self._elseBlockInstr))
        if elseBlk:
            code += ['} else {']
            code += elseBlk
        code += ['}']
        return code

class WhileLoop(Instr):
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
            vm.run(self._loopInstrs)

    def compile(self, vm):
        code = []

        code += ['while(1){']
        blockCode = vm.compile(self._condInstrs)
        blockCode += ['if(!(' + str(vm.comp_pop().value) +')){']
        blockCode += _indent(['break;'])
        blockCode += ['}']
        blockCode += vm.compile(self._loopInstrs)
        code += _indent(blockCode)
        code += ['}']

        return code



