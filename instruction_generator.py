from lark.visitors import Interpreter,  visit_children_decor
from instructions import *

def getSymValue(sym):
    assert sym.data == 'sym'
    return str(sym.children[0])


class InstructionGenerator(Interpreter):
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

    def func(self, tree):
        sym = getSymValue(tree.children[0])
        args = [getSymValue(arg) for arg in tree.children[1].children]
        # for arg in tree.children[1].children:
        #     args += [getSymValue(arg)]
        instrs = self.visit_get_instrs(tree.children[-1])
        self._vm.addFunc(sym, Func(sym, args, instrs))

    def func_call(self, tree):
        sym = getSymValue(tree.children[0])
        callArgs = tree.children[1].children
        argInstrs = [self.visit_get_instrs(exprn) for exprn in callArgs]
        self._vm.addInstr(Call(sym, argInstrs))

    @visit_children_decor
    def func_call_statement(self, tree):
        self._vm.addInstr(Pop())

    def rtn(self, tree):
        exprn = []
        if len(tree.children):
            exprn = self.visit_get_instrs(tree.children[0])
        self._vm.addInstr(Rtn(exprn))