#! /usr/bin/python3

from lark import Lark
from lark.visitors import Interpreter,  visit_children_decor
from collections import namedtuple





_Instr = namedtuple('Instr', ['op', 'data'])


def Instr(op, *vargs):
        return _Instr(op, vargs)


class VMRuntimeError(Exception):
    def __init__(self, desc):
        super().__init__(desc)

class VirtualMachine:
    def __init__(self):
        self._instrs = []
        self._dataStack = []
        self._ctx = {}


    def _push(self, data):
        self._dataStack.append(data)

    def _pop(self):
        return self._dataStack.pop()

    def addInstr(self, instr):
        self._instrs.append(instr)



    def __str__(self):
        return 'VM:\n\t' + str(self._instrs) + '\n\t' + str(self._dataStack) \
                + '\n\t' + str(self._ctx)

    def run(self):
        for instr in self._instrs:
            method = getattr(self, instr.op, None)
            if method is None:
                raise ValueError('Unrecognized instr.op: ' + instr.op)
            method(instr.data)




    def add(self, data):
        right = self._pop()
        left = self._pop()
        self._push(left + right)


    def sub(self, data):
        right = self._pop()
        left = self._pop()
        self._push(left - right)


    def mult(self, data):
        right = self._pop()
        left = self._pop()
        self._push(left * right)


    def div(self, data):
        right = self._pop()
        left = self._pop()
        self._push(left // right)


    def neg(self, data):
        arg = self._pop()
        self._push(arg * -1)


    def assign(self, data):
        sym = data[0]
        if sym not in self._ctx:
            raise VMRuntimeError('Attempt to assign to undeclared variable ' + sym)
        self._ctx[sym] = self._pop()


    def decl(self, data):
        sym = data[0]
        if sym in self._ctx:
            raise VMRuntimeError('Attempt to declare already declared vaiable ' + sym)
        self._ctx[sym] = 0


    def pushi(self, data):
        self._push(data[0])


    def push(self, data):
        self._push(self._ctx[data[0]])



def getSymValue(sym):
    assert sym.data == 'sym'
    return str(sym.children[0])


class TreeInterpreter(Interpreter):
    def __init__(self, vm):
        super().__init__()
        self._vm = vm

    @visit_children_decor
    def add(self, tree):
        self._vm.addInstr(Instr('add'))

    @visit_children_decor
    def sub(self, tree):
        self._vm.addInstr(Instr('sub'))

    @visit_children_decor
    def mult(self, tree):
        self._vm.addInstr(Instr('mult'))

    @visit_children_decor
    def div(self, tree):
        self._vm.addInstr(Instr('div'))

    @visit_children_decor
    def neg(self, tree):
        self._vm.addInstr(Instr('neg'))



    def assign(self, tree):
        self.visit(tree.children[1])
        self._vm.addInstr(Instr('assign', getSymValue(tree.children[0])))



    def num(self, tree):
        self._vm.addInstr(Instr('pushi', int(tree.children[0]) ))


    def sym(self, tree):
        self._vm.addInstr(Instr('push', getSymValue(tree)))


    def decl(self, tree):
        print('decl:', tree)
        self._vm.addInstr(Instr('decl', getSymValue(tree.children[0])))


    def decl_init(self, tree):
        self.visit(tree.children[1])
        self._vm.addInstr(Instr('decl',    getSymValue(tree.children[0])))
        self._vm.addInstr(Instr('assign',  getSymValue(tree.children[0])))






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


    print('---------------------------------------------------------------------')


if __name__ == '__main__':
    with  open('syntax.lark', 'r') as synfile:
        syntax = ''.join(synfile.readlines())

    parser = Lark(syntax)


    # run('''

    # var x;
    # '''
    # )

    # run('var x = 2;')

    # run('''
    #  var x;
    #  var x;
    # ''')

    run('''
        var x = 1;
        var y = x - 20 + 10 * 3 / 4;
        var z;
        var w = 3*(x+1);

    ''')

    # run('''

    # ''')

    # run('''

    # ''')

