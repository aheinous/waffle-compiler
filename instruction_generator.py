from collections import namedtuple
from lark.visitors import Interpreter,  visit_children_decor
from instructions import *

def getSymValue(sym):
    assert sym.data == 'sym'
    return str(sym.children[0])


_Position = namedtuple('Position', ['filename', 'ln', 'col'])

class Position(_Position):
    def __str__(self):
        return '{}:{}:{}'.format(self.filename, self.ln, self.col)



def add_pos_arg(func):
    def wrapper(self, tree):
        pos = Position(self._fname, tree.line, tree.column)
        func(self, tree, pos)
    return wrapper


class InstructionGenerator(Interpreter):
    def __init__(self, vm, fname):
        super().__init__()
        self._vm = vm
        self._fname = fname

    def visit_get_instrs(self, tree):
        with self._vm.newInstrDest() as instrDest:
            self.visit(tree)
            return instrDest.getInstrs()


    @add_pos_arg
    def add(self, tree, pos):
        self.visit_children(tree)
        self._vm.addInstr(Add(pos))


    @add_pos_arg
    def sub(self, tree, pos):
        self.visit_children(tree)
        self._vm.addInstr(Sub(pos))


    @add_pos_arg
    def mult(self, tree, pos):
        self.visit_children(tree)
        self._vm.addInstr(Mult(pos))


    @add_pos_arg
    def div(self, tree, pos):
        self.visit_children(tree)
        self._vm.addInstr(Div(pos))


    @add_pos_arg
    def neg(self, tree, pos):
        self.visit_children(tree)
        self._vm.addInstr(Neg(pos))



    @add_pos_arg
    def assign(self, tree, pos):
        self.visit(tree.children[1])
        self._vm.addInstr(Assign( getSymValue(tree.children[0]), pos ) )



    @add_pos_arg
    def num(self, tree, pos):
        self._vm.addInstr(Pushi( int(tree.children[0]), pos))


    @add_pos_arg
    def sym(self, tree, pos):
        self._vm.addInstr(Push( getSymValue(tree), pos))


    @add_pos_arg
    def decl(self, tree, pos):
        print('decl:', tree)
        self._vm.addInstr(Decl( getSymValue(tree.children[0]), pos))

    @add_pos_arg
    def decl_init(self, tree, pos):
        self.visit(tree.children[1])
        self._vm.addInstr(Decl( getSymValue(tree.children[0]), pos ))
        self._vm.addInstr(Assign( getSymValue(tree.children[0]), pos))


    @add_pos_arg
    def if_elif(self, tree, pos):
        children = tree.children
        elseBlk = []
        if len(children) % 2 == 1:
            elseBlk = self.visit_get_instrs(children[-1])

        start = len(children) - (len(children) % 2) - 2


        for i in range(start, -2, -2):
            cond =  self.visit_get_instrs(children[i])
            ifBlk = self.visit_get_instrs(children[i+1])
            elseBlk = [IfElse(cond, ifBlk, elseBlk, pos)]

        self._vm.addInstr(elseBlk[0])



    @add_pos_arg
    def while_loop(self, tree, pos):

        with self._vm.newInstrDest() as instrDest:
            self.visit(tree.children[0])
            cond = instrDest.getInstrs()

        with self._vm.newInstrDest() as instrDest:
            self.visit(tree.children[1])
            loop = instrDest.getInstrs()
        whileloop = WhileLoop(cond, loop)
        self._vm.addInstr(whileloop)

    @add_pos_arg
    def func(self, tree, pos):
        sym = getSymValue(tree.children[0])
        args = [getSymValue(arg) for arg in tree.children[1].children]
        # for arg in tree.children[1].children:
        #     args += [getSymValue(arg)]
        instrs = self.visit_get_instrs(tree.children[-1])
        func = Func(sym, args, instrs, pos)
        self._vm.addFunc(sym, func, func)

    @add_pos_arg
    def func_call(self, tree, pos):
        sym = getSymValue(tree.children[0])
        callArgs = tree.children[1].children
        argInstrs = [self.visit_get_instrs(exprn) for exprn in callArgs]
        self._vm.addInstr(Call(sym, argInstrs, pos))


    @add_pos_arg
    def func_call_statement(self, tree, pos):
        self.visit_children(tree)
        self._vm.addInstr(Pop(pos))

    @add_pos_arg
    def rtn(self, tree, pos):
        exprn = []
        if len(tree.children):
            exprn = self.visit_get_instrs(tree.children[0])
        self._vm.addInstr(Rtn(exprn, pos))