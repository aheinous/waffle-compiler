# from scope_mgr import ScopeMgr
from instruction_block import Block
from lark.visitors import Interpreter
from position import Position
from instructions import Func, Assign, Push, Pushi, Pop, Decl, IfElse, WhileLoop, Rtn, Call, BinOp, UnaryOp
from type_system import make_type, make_value, TypedValue, TypedSym, Add, Sub, Mul, Div, Neg, Int, Float, String

def _get_sym(sym):
    assert sym.data == 'sym'
    return str(sym.children[0])

def _get_type(type_, pos):
    assert type_.data == 'type'
    return make_type(str(type_.children[0]), pos)


def _get_sym_and_type(two_children, pos):
    return TypedSym(
        _get_sym(two_children[0]),
        _get_type(two_children[1], pos)
    )




def add_position_arg(func):
    def wrapper(self, tree):
        pos = Position(self._fname, tree.line, tree.column)
        func(self, tree, pos)
    return wrapper





class _InstructionRecorder:
    def __init__(self):
        self._instrn_stack = [Block()]

    def add_instrn(self, instrn):
        self._instrn_stack[-1].append(instrn)

    def push(self):
            self._instrn_stack.append(Block())

    def pop(self):
        return self._instrn_stack.pop()

class InstructionGenerator(Interpreter):
    def __init__(self, fname):
        super().__init__()
        self._fname = fname
        self._instrn_recorder = _InstructionRecorder()
        self._funcs = []

    @property
    def instructions(self):
        return self._instrn_recorder._instrn_stack[0]

    @property
    def functions(self):
        return self._funcs

    def _visit_get_instrs(self, tree):
        self._instrn_recorder.push()
        self.visit(tree)
        # instrns = self._instrn_recorder.instrns
        instrns = self._instrn_recorder.pop()
        return instrns

    @add_position_arg
    def add(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(Add(), pos))


    @add_position_arg
    def sub(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(Sub(), pos))


    @add_position_arg
    def mult(self, tree, pos):
        self.visit_children(tree)
        mul = Mul()
        binop = BinOp(mul, pos)
        self._instrn_recorder.add_instrn(binop)


    @add_position_arg
    def div(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(Div(), pos))


    @add_position_arg
    def neg(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(UnaryOp(Neg(), pos))



    @add_position_arg
    def assign(self, tree, pos):
        self.visit(tree.children[1])
        self._instrn_recorder.add_instrn(Assign( _get_sym(tree.children[0]), pos ) )



    @add_position_arg
    def integer(self, tree, pos):
        str_repr = str(tree.children[0])
        typed_value = make_value(str_repr, Int(), pos)
        self._instrn_recorder.add_instrn(Pushi(typed_value, pos))

    @add_position_arg
    def floating_pt(self, tree, pos):
        str_repr = str(tree.children[0])
        typed_value = make_value(str_repr, Float(), pos)
        self._instrn_recorder.add_instrn(Pushi(typed_value, pos))

    @add_position_arg
    def string(self, tree, pos):
        str_repr = str(tree.children[0])
        typed_value = make_value(str_repr, String(), pos)
        self._instrn_recorder.add_instrn(Pushi(typed_value, pos))



    @add_position_arg
    def sym(self, tree, pos):
        self._instrn_recorder.add_instrn(Push( _get_sym(tree), pos))


    @add_position_arg
    def decl(self, tree, pos):
        var = _get_sym_and_type(tree.children[0:2], pos)
        self._instrn_recorder.add_instrn(Decl( var, pos))

    @add_position_arg
    def decl_init(self, tree, pos):
        typed_sym = _get_sym_and_type(tree.children[0:2], pos)
        exprn = tree.children[2]
        self.visit(exprn)
        self._instrn_recorder.add_instrn(Decl( typed_sym, pos ))
        self._instrn_recorder.add_instrn(Assign( typed_sym.sym, pos))


    @add_position_arg
    def if_elif(self, tree, pos):
        children = tree.children
        elseBlk = Block()
        elsePos  = None
        if len(children) % 2 == 1: # if else block at end of if elif chain
            elseBlk = self._visit_get_instrs(children[-1])
            # elsePos =

        start = len(children) - (len(children) % 2) - 2


        for i in range(start, -2, -2):
            cond =  self._visit_get_instrs(children[i])
            ifBlk = self._visit_get_instrs(children[i+1])
            pos = cond[0].pos
            elseBlk = Block([IfElse(cond, ifBlk, elseBlk, pos)])

        self._instrn_recorder.add_instrn(elseBlk[0])



    @add_position_arg
    def while_loop(self, tree, pos):
        children = tree.children
        cond = self._visit_get_instrs(children[0])
        loop = self._visit_get_instrs(children[1])

        whileloop = WhileLoop(cond, loop, pos)
        self._instrn_recorder.add_instrn(whileloop)

    @add_position_arg
    def func(self, tree, pos):
        treeArgList = tree.children[1].children
        argList = []
        for i in range(0, len(treeArgList), 2):
            argList.append(_get_sym_and_type(treeArgList[i:i+2], pos))


        sym = _get_sym(tree.children[0])
        rtn_type = _get_type(tree.children[2], pos)

        block = tree.children[3]
        block = self._visit_get_instrs(block)

        '''make sure we end with a Rtn'''
        if not block or not isinstance(block[-1], Rtn):
            block += [Rtn([], pos)]
        typed_sym = TypedSym(sym, rtn_type)
        func = Func(typed_sym, argList, block, pos)
        typed_func = TypedValue(func, rtn_type)
        # self._instrn_recorder.init_symbol(typed_sym, typed_func, pos)
        self._funcs.append((typed_sym, typed_func))

    @add_position_arg
    def func_call(self, tree, pos):
        sym = _get_sym(tree.children[0])
        callArgs = tree.children[1].children
        argInstrs = [self._visit_get_instrs(exprn) for exprn in callArgs]
        self._instrn_recorder.add_instrn(Call(sym, argInstrs, pos))


    @add_position_arg
    def func_call_statement(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(Pop(pos))

    @add_position_arg
    def rtn(self, tree, pos):
        exprn = []
        if len(tree.children):
            exprn = self._visit_get_instrs(tree.children[0])
        self._instrn_recorder.add_instrn(Rtn(exprn, pos))