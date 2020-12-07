#! /usr/bin/python3

from lark import Lark
from lark.visitors import Interpreter,  visit_children_decor
from collections import namedtuple

def indent(strlist):
    for i in range(len(strlist)):
        strlist[i] = '\t' + strlist[i]
    return strlist

class Instr:
    def run(vm):
        pass
    def compile(vm):
        pass
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
        if self._sym not in vm.run_ctx:
            raise VMRuntimeError('Attempt to assign to undeclared variable ' + self._sym)
        vm.run_ctx[self._sym] = vm.run_pop()

    def compile(self, vm):
        return '{} = {};'.format(self._sym, vm.comp_pop())

class Decl(Instr):
    def __init__(self, sym):
        self._sym = sym

    def run(self, vm):
        if self._sym  in vm.run_ctx:
            raise VMRuntimeError('Attempt to declare already declared vaiable ' + self._sym)
        vm.run_ctx[self._sym] = 0

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

# class IfStatement(Instr):
#     def __init__(self, instrs):
#         self._instrs = instrs

#     def run(self, vm):
#         cond = vm.run_pop()
#         if(cond):
#             vm.run(self._instrs)

#     def compile(self, vm):
#         code = ['if(' + vm.comp_pop() + '){']
#         block = vm.compile(self._instrs)
#         indent(block)
#         code += block
#         code += ['}']
#         return code


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
        code += indent(vm.compile(self._ifBlockInstr))
        elseBlk = indent(vm.compile(self._elseBlockInstr))
        if elseBlk:
            code += ['} else {']
            # code += indent(vm.compile(self._elseBlockInstr))
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

        # condCode= vm.compile(self._condInstrs)
        # code += condCode
        # code += ['while(' + vm.comp_pop() + '){']
        # blockCode = vm.compile(self._loopInstrs)
        # blockCode += condCode
        # indent(blockCode)
        # code += blockCode
        # code += ['}']

        code += ['while(1){']
        blockCode = vm.compile(self._condInstrs)
        blockCode += ['if(!(' + vm.comp_pop()+')){']
        blockCode += indent(['break;'])
        blockCode += ['}']
        blockCode += vm.compile(self._loopInstrs)
        code += indent(blockCode)
        code += ['}']

        return code





class RAIIInstrDest:
    def __init__(self, vm, instrs):
        self._vm = vm
        self._instrs = instrs

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        # print('__exit__: ', self, vargs)
        self._vm._popInstrDest()

    def getInstrs(self):
        return self._instrs


class VMRuntimeError(Exception):
    def __init__(self, desc):
        super().__init__(desc)

class VirtualMachine:
    def __init__(self):
        self._instrsDestStack = [[]]

        self._run_dataStack = []
        self.run_ctx = {}

        self.comp_varStack = []
        self.comp_varCnt = 0

    def comp_push(self, val):
        name = 'tmp_{}'.format(self.comp_varCnt)
        self.comp_varStack.append(name)
        code = 'int {} = {};'.format(name, val)
        self.comp_varCnt += 1
        return code

    def comp_pushi(self, val):
        self.comp_varStack.append(str(val))
        return []

    # def comp_pushSym(self, val):
    #     self.comp_varStack.append(str(val))
    #     return []



    def comp_pop(self):
        return self.comp_varStack.pop()


    def run_push(self, data):
        self._run_dataStack.append(data)

    def run_pop(self):
        return self._run_dataStack.pop()

    def addInstr(self, instr):
        self._instrs().append(instr)

    # def addIn

    def _instrs(self):
        return self._instrsDestStack[-1]

    def newInstrDest(self):
        self._instrsDestStack.append([])
        return RAIIInstrDest(self, self._instrsDestStack[-1])

    def _popInstrDest(self):
        self._instrsDestStack.pop()


    def __str__(self):
        return 'VM:\n\t' + str(self._instrs()) + '\n\t' + str(self._run_dataStack) \
                + '\n\t' + str(self.run_ctx)


    def run(self, instrs=None):
        if instrs is None:
            instrs = self._instrs()
        for instr in instrs:
            instr.run(self)

    def compile(self, instrs=None):
        if instrs is None:
            instrs = self._instrs()
        code = []
        for instr in instrs:
            instrCode = instr.compile(self)
            if isinstance(instrCode, str):
                code.append(instrCode)
            else:
                assert isinstance(instrCode, list)
                code += instrCode
        return code




def getSymValue(sym):
    assert sym.data == 'sym'
    return str(sym.children[0])


class TreeInterpreter(Interpreter):
    def __init__(self, vm):
        super().__init__()
        self._vm = vm

    def visit_get_instrs(self, tree):
        with self._vm.newInstrDest() as instrDest:
            self.visit(tree)
            return instrDest.getInstrs()

    @visit_children_decor
    def add(self, tree):
        self._vm.addInstr(Add())

    @visit_children_decor
    def sub(self, tree):
        self._vm.addInstr(Sub())

    @visit_children_decor
    def mult(self, tree):
        self._vm.addInstr(Mult())

    @visit_children_decor
    def div(self, tree):
        self._vm.addInstr(Div())

    @visit_children_decor
    def neg(self, tree):
        self._vm.addInstr(Neg())



    def assign(self, tree):
        self.visit(tree.children[1])
        self._vm.addInstr(Assign( getSymValue(tree.children[0])))



    def num(self, tree):
        self._vm.addInstr(Pushi( int(tree.children[0]) ))


    def sym(self, tree):
        self._vm.addInstr(Push( getSymValue(tree)))


    def decl(self, tree):
        print('decl:', tree)
        self._vm.addInstr(Decl( getSymValue(tree.children[0])))

    def decl_init(self, tree):
        self.visit(tree.children[1])
        self._vm.addInstr(Decl( getSymValue(tree.children[0])))
        self._vm.addInstr(Assign( getSymValue(tree.children[0])))


    # def if_statement(self, tree):
    #     self.visit(tree.children[0])
    #     with self._vm.newInstrDest() as instrDest:
    #         self.visit(tree.children[1])
    #         ifstatement = IfStatement(instrDest.getInstrs())
    #     self._vm.addInstr(ifstatement)

    def if_elif(self, tree):
        children = tree.children
        elseBlk = []
        if len(children) % 2 == 1:
            elseBlk = self.visit_get_instrs(children[-1])

        start = len(children) - (len(children) % 2) - 2


        for i in range(start, -2, -2):
            cond =  self.visit_get_instrs(children[i])
            ifBlk = self.visit_get_instrs(children[i+1])
            elseBlk = [IfElse(cond, ifBlk, elseBlk)]

        self._vm.addInstr(elseBlk[0])



    def while_loop(self, tree):

        with self._vm.newInstrDest() as instrDest:
            self.visit(tree.children[0])
            cond = instrDest.getInstrs()

        with self._vm.newInstrDest() as instrDest:
            self.visit(tree.children[1])
            loop = instrDest.getInstrs()
        whileloop = WhileLoop(cond, loop)
        self._vm.addInstr(whileloop)






def run(exprn):

    print('---------------------------------------------------------------------')
    print(exprn)
    tree = parser.parse(exprn)
    print('### tree')
    print(tree)
    print(tree.pretty())


    print("### Tree interpreter")
    vm = VirtualMachine()
    ti = TreeInterpreter(vm)

    ti.visit(tree)
    print(vm)

    print('### Run')
    try:
        vm.run()
    except VMRuntimeError as rte:
        print('ERROR: ' + str(rte))

    print(vm)


    print('### compile')
    code = '\n'.join(vm.compile())
    print(code)

    print(exprn)


    print('---------------------------------------------------------------------')


if __name__ == '__main__':
    with  open('syntax.lark', 'r') as synfile:
        syntax = ''.join(synfile.readlines())

    parser = Lark(syntax)


    run('''

    var x = 2 + 3;
    '''
    )

    # run('var x = 2;')

    # run('''
    #  var x;
    #  var x;
    # ''')

    run('''
        var x = 1 * (3+4) - 1000 +10;

    ''')

    run('''
        var y;
        var x = 1 + 2 * 3 / 2 - 1;
        y = 1;
        var z = y - x;
    ''')

    run('''
        var z = 1;
        if(0 + z){
            z = 2 + 0;
            z = (2*z) / 2 + 1;
        }
        var y = 3 + z;
    ''')

    run('''
        var z = 1;
        if(0 + z){
            z = 2 + 0;
            z = (2*z) / 2 + 1;
            if(z){
                z = z+1;
            }
        }
        var y = 3 + z;
    ''')


    run('''
        var accum = 1;
        var num = 5;
        while(num+2){
            accum = accum*2;
            num = num -1;
        }
    ''')


    run('''
        var x = 2;
        var y;
        if(x-2){
            y =1;
        }elif(x){
            y = 2;
        } elif(x-3) {
            y = 3;
            y = y + 1;
        }else{
            y = 400;
        }

    ''')

    run('''
        if(2){
            var x = 3;
        } else {

        }
    ''')

    # run('''
    # if(2){

    # }
    # ''')
