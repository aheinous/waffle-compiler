
def _indent(strlist):
    for i in range(len(strlist)):
        strlist[i] = '\t' + strlist[i]
    return strlist


class Instr:
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
    def __init__(self, sym):
        self._sym = sym

    def run(self, vm):
        # if self._sym not in vm.run_ctx:
        #     raise VMRuntimeError('Attempt to assign to undeclared variable ' + self._sym)
        # vm.run_ctx[self._sym] = vm.run_pop()

        vm.run_ctx.assign(self._sym, vm.run_pop())

    def compile(self, vm):
        return '{} = {};'.format(self._sym, vm.comp_pop())

class Decl(Instr):
    def __init__(self, sym):
        self._sym = sym

    def run(self, vm):
        # print('sym:',self._sym)
        # if self._sym in vm.run_ctx.local_scope:
        #     raise VMRuntimeError('Attempt to declare already declared vaiable ' + self._sym)
        # vm.run_ctx[self._sym] = 0
        vm.run_ctx.decl(self._sym, 0)

    def compile(self, vm):
        return 'int {} = 0;'.format(self._sym)


class Pushi(Instr):
    def __init__(self, value):
        self._value = value

    def run(self, vm):
        vm.run_push(self._value)

    def compile(self, vm):
        code = vm.comp_pushi(self._value)
        return code

class Push(Instr):
    def __init__(self, sym):
        self._sym = sym

    def run(self, vm):
        vm.run_push(vm.run_ctx[self._sym])

    def compile(self, vm):
        return vm.comp_pushi(self._sym)

class RtnException(Exception):
    pass


class Func:
    def __init__(self, sym, args, instrs):
        self._sym = sym
        self._args = args
        self._instrs = instrs

    def run(self, vm):
        vm.run_ctx.push()
        for argName in reversed(self._args):
            vm.run_ctx.decl(argName, vm.run_pop())
        try:
            vm.run(self._instrs)
        except RtnException as e:
            pass
        vm.run_ctx.pop()

    def compile(self, vm):
        code = ['void {}({}){{\n'.format(self._sym, ', '.join(('int ' + a for a in self._args)))]
        code += _indent(vm.compile(self._instrs))
        code += ['}']
        return code

class Call(Instr):
    def __init__(self, sym, argExprns):
        self._sym = sym
        self._argExprns = argExprns

    def run(self, vm):
        for instrs in self._argExprns:
            vm.run(instrs)
        vm.call(self._sym)

    def compile(self, vm):
        callCode = ''
        code = []
        for argExprn in self._argExprns:
            code += vm.compile(argExprn)
            # callCode = vm.comp_pop() + (', '  if callCode else '')
            callCode += (', '  if callCode else '') + vm.comp_pop()

        vm.comp_pushi( self._sym + '(' + callCode + ')' )
        return code

class Rtn(Instr):
    def __init__(self, exprn):
        self._exprn = exprn

    def run(self, vm):
        vm.run(self._exprn)
        raise RtnException()

    def compile(self, vm):
        vm.compile(self._exprn)
        return 'return ' + vm.comp_pop() + ';'

class Pop(Instr):
    def run(self, vm):
        vm.run_pop()

    def compile(self, vm):
        vm.comp_pop()
        return ''


class IfElse(Instr):
    def __init__(self, condInstr, ifBlockInstr, elseBlockInstr):
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
    def __init__(self, condInstrs, loopInstrs):
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



