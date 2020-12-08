
from collections import namedtuple
from exceptions import RtnException, VMRuntimeException


def _indent(strlist):
    for i in range(len(strlist)):
        strlist[i] = '\t' + strlist[i]
    return strlist



class VoidType:
    def __eq__(self, o: object) -> bool:
        return isinstance(o, VoidType)

    def __str__(self):
        return "Void"


Void = VoidType()
TypedValue = namedtuple('TypedValue', ['value', 'vtype'])


class Func:
    def __init__(self, name, args, instrs, pos):
        self._name = name
        self._args = args
        self._instrs = instrs
        self.pos = pos

    def run(self, vm):
        vm.run_ctx.push()
        for arg in reversed(self._args):
            vm.run_ctx.decl(arg, vm.run_pop(), self)
        try:
            vm.run(self._instrs)
        except RtnException as e:
            pass
        vm.run_ctx.pop()

    def compile(self, vm):
        argList = ', '.join(('{} {}'.format(a.vtype, a.value) for a in self._args))
        code = ['{} {}({}){{\n'.format(self._name.vtype, self._name.value, argList)]


        code += _indent(vm.compile(self._instrs))
        code += ['}']
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
        vm.run_push(left + right)

    def compile(self, vm):
        right = vm.comp_pop()
        left = vm.comp_pop()
        return vm.comp_push('{} + {}'.format(left, right))

class Sub(Instr):
    def run(self, vm):
        right = vm.run_pop()
        left = vm.run_pop()
        vm.run_push(left - right)

    def compile(self, vm):
        right = vm.comp_pop()
        left = vm.comp_pop()
        return vm.comp_push('{} - {}'.format(left, right))

class Mult(Instr):
    def run(self, vm):
        right = vm.run_pop()
        left = vm.run_pop()
        vm.run_push(left * right)

    def compile(self, vm):
        right = vm.comp_pop()
        left = vm.comp_pop()
        return vm.comp_push('{} * {}'.format(left, right))

class Div(Instr):
    def run(self, vm):
        right = vm.run_pop()
        left = vm.run_pop()
        vm.run_push(left // right)

    def compile(self, vm):
        right = vm.comp_pop()
        left = vm.comp_pop()
        return vm.comp_push('{} / {}'.format(left, right))


class Neg(Instr):
    def run(self, vm):
        operand = vm.run_pop()
        vm.run_push(-operand)

    def compile(self, vm):
        operand = vm.comp_pop()
        return vm.comp_push('-{}'.format(operand))


class Assign(Instr):
    def __init__(self, name, pos):
        super().__init__(pos)
        self._name = name

    def run(self, vm):
        val = vm.run_pop()
        if val is Void:
            raise VMRuntimeException('Assigning a value of void', self.pos)
        vm.run_ctx.assign(self._name, val, self)

    def compile(self, vm):
        val = vm.comp_pop()
        # print('assign ', val)
        if val is Void:
            raise VMRuntimeException('Assigning a value of void', self.pos)
        return '{} = {};'.format(self._name.value, val)

class Decl(Instr):
    def __init__(self, var, pos):
        super().__init__(pos)
        self._var = var

    def run(self, vm):
        vm.run_ctx.decl(self._var, 0, self)

    def compile(self, vm):
        return 'int {} = 0;'.format(self._var.value)


class Pushi(Instr):
    def __init__(self, value, pos):
        super().__init__(pos)
        self._value = value

    def run(self, vm):
        vm.run_push(self._value)

    def compile(self, vm):
        code = vm.comp_pushi(self._value)
        return code


class Push(Instr):
    def __init__(self, sym, pos):
        super().__init__(pos)
        self._sym = sym

    def run(self, vm):
        vm.run_push(vm.run_ctx.get(self._sym, self))

    def compile(self, vm):
        return vm.comp_pushi(self._sym)


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
        callCode = ''
        code = []
        for argExprn in self._argExprns:
            code += vm.compile(argExprn)
            callCode += (', '  if callCode else '') + vm.comp_pop()

        vm.comp_pushi( self._sym + '(' + callCode + ')' )
        return code

class Rtn(Instr):
    def __init__(self, exprn, pos):
        super().__init__(pos)
        self._exprn = exprn

    def run(self, vm):
        if self._exprn:
            vm.run(self._exprn)
        else:
            vm.run_push(Void)
        raise RtnException()

    def compile(self, vm):
        if self._exprn:
            code = vm.compile(self._exprn)
            code += ['return ' + vm.comp_pop() + ';']
            return code
        return 'return;'

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
        cond = vm.run_pop()
        if cond:
            vm.run(self._ifBlockInstr)
        else:
            vm.run(self._elseBlockInstr)

    def compile(self, vm):
        code = vm.compile(self._condInstr)
        code += ['if(' + vm.comp_pop() + '){']
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
            if not cond:
                break
            vm.run(self._loopInstrs)

    def compile(self, vm):
        code = []

        code += ['while(1){']
        blockCode = vm.compile(self._condInstrs)
        blockCode += ['if(!(' + vm.comp_pop()+')){']
        blockCode += _indent(['break;'])
        blockCode += ['}']
        blockCode += vm.compile(self._loopInstrs)
        code += _indent(blockCode)
        code += ['}']

        return code



