from typed_data import TSym, RValue, regNewType, typeFromString
from instruction_block import Block
from lark.visitors import Interpreter
from position import Position
from instructions import (  ClassDecl, Func, Assign, InitFunc, Mixin, MixinStatements,
                            ObjectInit, PLocal, Push, Pushi, Pop, Decl, IfElse, WhileLoop, Rtn,
                            Call, BinOp, UnaryOp )
from type_system import (   And, Eq, Gt, GtEq, Lt, LtEq, NotEq, Or,  Add, Sub, Mul,
                            Div, Neg, Int, Float, String )
import type_system as type_sys

def _get_sym(sym):
    assert sym.data == 'sym'
    return str(sym.children[0])

def _get_type(type_, pos):
    assert type_.data == 'type'
    return typeFromString(str(type_.children[0]), pos)


def _get_sym_and_type(two_children, pos):
    return TSym(
        _get_sym(two_children[0]),
        _get_type(two_children[1], pos)
    )


def add_position_arg(func):
    def wrapper(self, tree):
        pos = Position(self._fname, tree.line, tree.column, tree.end_line, tree.end_column)
        func(self, tree, pos)
    return wrapper



class _InstructionRecorder:
    def __init__(self):
        self.reset()

    def add_instrn(self, instrn):
        self._instrn_stack[-1].append(instrn)

    def push(self):
            self._instrn_stack.append(Block())

    def pop(self):
        return self._instrn_stack.pop()

    def reset(self):
        self._instrn_stack = [Block()]



class InstructionGenerator(Interpreter):
    def __init__(self):
        super().__init__()
        self._fname = None
        self._instrn_recorder = _InstructionRecorder()
        self._funcs = []

    def gen_instrn_tree(self, ast, src_fname):
        self._fname = src_fname
        self.visit(ast)
        tree = self._instrn_recorder.pop()
        self._instrn_recorder.reset()
        return tree

    @property
    def functions(self):
        return self._funcs

    def _visit_get_instrs(self, tree):
        self._instrn_recorder.push()
        if len(tree.children):
            self.visit(tree)
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
    def eq(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(Eq(), pos))
    @add_position_arg
    def not_eq(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(NotEq(), pos))
    @add_position_arg
    def gt(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(Gt(), pos))
    @add_position_arg
    def gteq(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(GtEq(), pos))
    @add_position_arg
    def lt(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(Lt(), pos))
    @add_position_arg
    def lteq(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(LtEq(), pos))
    @add_position_arg
    def and_exprn(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(And(), pos))
    @add_position_arg
    def or_exprn(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(BinOp(Or(), pos))

    @add_position_arg
    def assign(self, tree, pos):
        self.visit_children(tree)
        self._instrn_recorder.add_instrn(Assign(pos))



    @add_position_arg
    def integer(self, tree, pos):
        str_repr = str(tree.children[0])
        typed_value = RValue.fromString(str_repr, Int(), pos)
        self._instrn_recorder.add_instrn(Pushi(typed_value, pos))

    @add_position_arg
    def floating_pt(self, tree, pos):
        str_repr = str(tree.children[0])
        typed_value = RValue.fromString(str_repr, Float(), pos)
        self._instrn_recorder.add_instrn(Pushi(typed_value, pos))

    @add_position_arg
    def string(self, tree, pos):
        str_repr = str(tree.children[0])
        typed_value = RValue.fromString(str_repr, String(), pos)
        self._instrn_recorder.add_instrn(Pushi(typed_value, pos))


    @add_position_arg
    def multiline_string(self, tree, pos):
        str_repr = str(tree.children[0])[2:-2]
        typed_value = RValue.fromString(str_repr, String(), pos)
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
        self._instrn_recorder.add_instrn(Decl( typed_sym, pos ))
        self._instrn_recorder.add_instrn(Push( typed_sym.sym, pos))
        self.visit(exprn)
        self._instrn_recorder.add_instrn(Assign(pos))


# '''
#   func
#     sym main
#     decl_arg_list
#     type        int
#     block
#       if_statement
#         sym     x
#         block
#         assign
#           sym   z
#           integer       4
#       if_statement
#         sym     x
#         block
#         elif
#           integer       4
#           assign
#             sym z
#             integer     4
#           block
#       rtn
#         integer 0

# '''

    @add_position_arg
    def if_statement(self, tree, pos):
        # children[0] is void
        cond = self._visit_get_instrs(tree.children[1])
        ifBlk = self._visit_get_instrs(tree.children[2])
        elseBlk = self._visit_get_instrs(tree.children[3])

        self._instrn_recorder.add_instrn(IfElse(cond, ifBlk, elseBlk, pos))

    @add_position_arg
    def elif_statement(self, tree, pos):
        cond = self._visit_get_instrs(tree.children[1])
        ifBlk = self._visit_get_instrs(tree.children[2])
        elseBlk = self._visit_get_instrs(tree.children[3]) if len(tree.children) >= 4 else Block()

        self._instrn_recorder.add_instrn(IfElse(cond, ifBlk, elseBlk, pos))



    # @add_position_arg
    # def if_elif(self, tree, pos):
    #     children = tree.children
    #     elseBlk = Block()
    #     if len(children) % 2 == 0: # if else block at end of if elif chain
    #         elseBlk = self._visit_get_instrs(children[-1])

    #     start = len(children) - (len(children) % 2) - 2


    #     for i in range(start, -2, -2):
    #         cond =  self._visit_get_instrs(children[i])
    #         ifBlk = self._visit_get_instrs(children[i+1])
    #         pos = cond[0].pos
    #         elseBlk = Block([IfElse(cond, ifBlk, elseBlk, pos)])

    #     self._instrn_recorder.add_instrn(elseBlk[0])



    @add_position_arg
    def while_loop(self, tree, pos):
        children = tree.children
        cond = self._visit_get_instrs(children[1])
        loop = self._visit_get_instrs(children[2])

        whileloop = WhileLoop(cond, loop, pos)
        self._instrn_recorder.add_instrn(whileloop)

    @add_position_arg
    def func(self, tree, pos):

        modifier_list = tree.children[0] # not implemented yet
        func_type = tree.children[1]
        sym = tree.children[2]
        rtn_type = tree.children[3]
        treeArgList = tree.children[4]
        block = tree.children[5]

        func_type = func_type.data # not implemented yet

        #  get args
        treeArgList = treeArgList.children
        argTSyms = []
        argTypes = []
        for item in treeArgList:
            argTSyms.append(_get_sym_and_type(item.children, pos))
            argTypes.append(_get_type(item.children[1], pos))


        # get sym and rtn type
        sym = _get_sym(sym)
        # rtn_type = _get_type(tree.children[2], pos)
        rtn_type = _get_type(rtn_type, pos)

        # init type
        type_ = type_sys.Function(argTypes, rtn_type)

        # get block instructions
        # block = tree.children[3]
        block = self._visit_get_instrs(block)

        # make sure we end with a Rtn
        if not block or not isinstance(block[-1], Rtn):
            block += [Rtn([], pos)]

        # a function is a symbol, an arglist, and a block of code
        typed_sym = TSym(sym, type_)
        func = Func(typed_sym, argTSyms, block, pos)
        typed_func = RValue(func, type_)

        self._instrn_recorder.add_instrn(InitFunc(typed_sym, typed_func, pos))

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

    @add_position_arg
    def mixin_exprn(self, tree, pos):
        exprn = self._visit_get_instrs(tree.children[0])
        self._instrn_recorder.add_instrn(Mixin(exprn, pos))

    @add_position_arg
    def mixin_statement(self, tree, pos):
        statements = self._visit_get_instrs(tree.children[0])
        self._instrn_recorder.add_instrn(MixinStatements(statements, pos))


    @add_position_arg
    def class_decl(self, tree, pos):
        sym = _get_sym(tree.children[0])
        contents = self._visit_get_instrs(tree.children[1])

        uid = contents.uid

        type_ = type_sys.Class(sym, uid)

        # new type
        regNewType(sym, type_)

        # make init function
        tsym = TSym(sym, type_)
        # arg_list = []
        # preUsrInit = Block( [ObjectInit(type_, pos)] )
        # rtn = Rtn(rtn_exprn, pos)
        # init_block = Block([rtn])

        # init_func = Func(tsym, arg_list, init_block, pos)
        # t_init_func = RValue(init_func, type_)

        # ClassDecl registers init function
        self._instrn_recorder.add_instrn(ClassDecl(tsym,  contents, pos))

    @add_position_arg
    def class_content(self, tree, pos):
        self.visit_children(tree)

    @add_position_arg
    def plocal(self, tree, pos):
        self._instrn_recorder.add_instrn(PLocal(pos))



