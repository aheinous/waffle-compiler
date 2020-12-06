#! /usr/bin/python3

from os import name
from lark import Lark
from lark.visitors import Interpreter, Transformer, visit_children_decor

from collections import namedtuple


# json_parser = Lark(r"""
#     ?value: dict
#           | list
#           | string
#           | SIGNED_NUMBER      -> number
#           | "true"             -> true
#           | "false"            -> false
#           | "null"             -> null

#     list : "[" [value ("," value)*] "]"

#     dict : "{" [pair ("," pair)*] "}"
#     pair : string ":" value

#     string : ESCAPED_STRING

#     %import common.ESCAPED_STRING
#     %import common.SIGNED_NUMBER
#     %import common.WS
#     %ignore WS

#     """, start='value')

# text = '{"key": ["item0", "item1", 3.14], "true":null, "false":false}'
# tree = json_parser.parse(text)
# print(tree.pretty())


with  open('syntax.lark', 'r') as synfile:
    syntax = ''.join(synfile.readlines())

# print(syntax)

parser = Lark(syntax)


Sym = namedtuple('Sym', ['value'])

_Cmd = namedtuple('Cmd', ['op', 'data'])


def Cmd(op, *vargs):
        return _Cmd(op, vargs)


class VMRuntimeError(Exception):
    def __init__(self, desc):
        super().__init__(desc)

class VirtualMachine:
    def __init__(self):
        self._cmds = []
        self._dataStack = []
        self._ctx = {}

    def addCmd(self, cmd):
        self._cmds.append(cmd)

    def _pushData(self, data):
        self._dataStack.append(data)


    def __str__(self):
        return 'VM:\n\t' + str(self._cmds) + '\n\t' + str(self._dataStack) \
                + '\n\t' + str(self._ctx)

    def run(self):
        for cmd in self._cmds:
            if(cmd.op == 'add'):
                right = self._dataStack.pop()
                left = self._dataStack.pop()
                self._dataStack.append(left + right)
            elif(cmd.op == 'sub'):
                right = self._dataStack.pop()
                left = self._dataStack.pop()
                self._dataStack.append(left - right)
            elif(cmd.op == 'mult'):
                right = self._dataStack.pop()
                left = self._dataStack.pop()
                self._dataStack.append(left * right)
            elif(cmd.op == 'div'):
                right = self._dataStack.pop()
                left = self._dataStack.pop()
                self._dataStack.append(left // right)
            elif(cmd.op == 'neg'):
                arg = self._dataStack.pop()
                self._dataStack.append(arg * -1)

            elif(cmd.op == 'assign'):
                sym = cmd.data[0]
                if sym not in self._ctx:
                    raise VMRuntimeError('Attempt to assign to undeclared variable ' + sym)
                self._ctx[sym] = self._dataStack.pop()
            elif(cmd.op == 'decl'):
                sym = cmd.data[0]
                if sym in self._ctx:
                    raise VMRuntimeError('Attempt to declare already declared vaiable ' + sym)
                self._ctx[sym] = 0



            elif(cmd.op == 'pushi'):
                self._dataStack.append(cmd.data[0])
            elif(cmd.op == 'push'):
                self._dataStack.append(self._ctx[cmd.data[0]])

            else:
                raise ValueError('Unrecognized cmd.op: ' + cmd.op)
        # assert len(self._dataStack) == 1
        # return self._dataStack.pop()



class TreeInterpreter(Interpreter):
    def __init__(self, vm):
        super().__init__()
        self._vm = vm

    @visit_children_decor
    def add(self, tree):
        print('visit add')


    @visit_children_decor
    def sub(self, tree):
        self._vm.addCmd(Cmd('sub'))

    @visit_children_decor
    def mult(self, tree):
        self._vm.addCmd(Cmd('mult'))

    @visit_children_decor
    def div(self, tree):
        self._vm.addCmd(Cmd('div'))

    @visit_children_decor
    def neg(self, tree):
        self._vm.addCmd(Cmd('neg'))



    def assign(self, tree):
        self.visit(tree.children[1])
        sym = tree.children[0]
        assert sym.data == 'sym'
        # evaluate(children[1], vm)
        self._vm.addCmd(Cmd('assign', str(sym)))



    def num(self, tree):
        self._vm.addCmd(Cmd('pushi', int(tree.children[0]) ))


    def sym(self, tree):
        # print(tree)
        # print(children)
        self._vm.addCmd(Cmd('push', str( tree.children[0])))



    def decl(self, tree):
        print('decl:', tree)
        self._vm.addCmd(Cmd('decl', tree.children[0].value))


    def decl_init(self, tree):
        # evaluate(tree.children[1], self._vm)
        self.visit(tree.children[1])
        self._vm.addCmd(Cmd('decl', tree.children[0].value))
        self._vm.addCmd(Cmd('assign',  tree.children[0].value))


class PreInterpTransformer(Transformer):
    def sym(self, tree):
        return Sym(str(tree[0]))



def run(exprn):

    print('---------------------------------------------------------------------')
    print(exprn)
    tree = parser.parse(exprn)
    print('### tree')
    print(tree)
    print(tree.pretty())

    print('### PreinterpTransformation')
    preInterp = PreInterpTransformer()
    tree = preInterp.transform((tree))
    print(tree)
    print(tree.pretty())


    print("### Tree interpreter")
    vm = VirtualMachine()
    ti = TreeInterpreter(vm)

    ti.visit(tree)
    print('vm')

    print('### Run')
    try:
        vm.run()
    except VMRuntimeError as rte:
        print('ERROR: ' + str(rte))

    print(vm)


    print('---------------------------------------------------------------------')





run('''

var x;
'''
)

run('var x = 2;')

run('''
 var x;
 var x;
''')

run('''

''')

run('''

''')

run('''

''')

