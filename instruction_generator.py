from scope_mgr import ScopeMgr
from lark.visitors import Interpreter
from instructions import *
from type_system import *
from position import Position

# import re
# import codecs

# _ESCAPE_SEQUENCE_RE = re.compile(r'''
#     ( \\U........      # 8-digit hex escapes
#     | \\u....          # 4-digit hex escapes
#     | \\x..            # 2-digit hex escapes
#     | \\[0-7]{1,3}     # Octal escapes
#     | \\N\{[^}]+\}     # Unicode characters by name
#     | \\[\\'"abfnrtv]  # Single-character escapes
#     )''', re.UNICODE | re.VERBOSE)

# def _decode_escapes(s):
#     def decode_match(match):
#         return codecs.decode(match.group(0), 'unicode-escape')

#     return _ESCAPE_SEQUENCE_RE.sub(decode_match, s)

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


class InstructionGenerator(Interpreter):
    def __init__(self, fname):
        super().__init__()
        self._fname = fname
        self._scope_mgr = ScopeMgr()

    @property
    def results(self):
        return self._scope_mgr

    def _visit_get_instrs(self, tree):
        self._scope_mgr.push_scope()
        self.visit(tree)
        instrns = self._scope_mgr.instrns
        self._scope_mgr.pop_scope()
        return instrns

    @add_position_arg
    def add(self, tree, pos):
        self.visit_children(tree)
        self._scope_mgr.add_instrn(BinOp(Add(), pos))


    @add_position_arg
    def sub(self, tree, pos):
        self.visit_children(tree)
        self._scope_mgr.add_instrn(BinOp(Sub(), pos))


    @add_position_arg
    def mult(self, tree, pos):
        self.visit_children(tree)
        mul = Mul()
        binop = BinOp(mul, pos)
        # self._scope_mgr.add_instrn(BinOp(Mul(), pos))
        self._scope_mgr.add_instrn(binop)


    @add_position_arg
    def div(self, tree, pos):
        self.visit_children(tree)
        self._scope_mgr.add_instrn(BinOp(Div(), pos))


    @add_position_arg
    def neg(self, tree, pos):
        self.visit_children(tree)
        self._scope_mgr.add_instrn(UnaryOp(Neg(), pos))



    @add_position_arg
    def assign(self, tree, pos):
        self.visit(tree.children[1])
        self._scope_mgr.add_instrn(Assign( _get_sym(tree.children[0]), pos ) )



    @add_position_arg
    def integer(self, tree, pos):
        str_repr = str(tree.children[0])
        typed_value = make_value(str_repr, Int(), pos)

        # self._scope_mgr.add_instrn(Pushi( TypedValue(int(tree.children[0]), Int()), pos))
        self._scope_mgr.add_instrn(Pushi(typed_value, pos))

    @add_position_arg
    def floating_pt(self, tree, pos):
        str_repr = str(tree.children[0])
        typed_value = make_value(str_repr, Float(), pos)
        # self._scope_mgr.add_instrn(Pushi( TypedValue(float(tree.children[0]), Float()), pos))
        self._scope_mgr.add_instrn(Pushi(typed_value, pos))

    @add_position_arg
    def string(self, tree, pos):
        str_repr = str(tree.children[0])
        typed_value = make_value(str_repr, String(), pos)
        # s = str(tree.children[0])
        # s = _decode_escapes(str(tree.children[0])[1:-1])
        # print(s)
        # self._scope_mgr.add_instrn(Pushi( TypedValue(s, String), pos))
        self._scope_mgr.add_instrn(Pushi(typed_value, pos))



    @add_position_arg
    def sym(self, tree, pos):
        self._scope_mgr.add_instrn(Push( _get_sym(tree), pos))


    @add_position_arg
    def decl(self, tree, pos):
        var = _get_sym_and_type(tree.children[0:2], pos)
        self._scope_mgr.add_instrn(Decl( var, pos))

    @add_position_arg
    def decl_init(self, tree, pos):
        typed_sym = _get_sym_and_type(tree.children[0:2], pos)
        exprn = tree.children[2]
        self.visit(exprn)
        self._scope_mgr.add_instrn(Decl( typed_sym, pos ))
        self._scope_mgr.add_instrn(Assign( typed_sym.sym, pos))


    @add_position_arg
    def if_elif(self, tree, pos):
        children = tree.children
        elseBlk = []
        if len(children) % 2 == 1:
            elseBlk = self._visit_get_instrs(children[-1])

        start = len(children) - (len(children) % 2) - 2


        for i in range(start, -2, -2):
            cond =  self._visit_get_instrs(children[i])
            ifBlk = self._visit_get_instrs(children[i+1])
            elseBlk = [IfElse(cond, ifBlk, elseBlk, pos)]

        self._scope_mgr.add_instrn(elseBlk[0])



    @add_position_arg
    def while_loop(self, tree, pos):

        # with self._vm.newInstrDest() as instrDest:
        #     self.visit(tree.children[0])
        #     cond = instrDest.getInstrs()

        # with self._vm.newInstrDest() as instrDest:
        #     self.visit(tree.children[1])
        #     loop = instrDest.getInstrs()
        children = tree.children
        cond = self._visit_get_instrs(children[0])
        loop = self._visit_get_instrs(children[1])

        whileloop = WhileLoop(cond, loop, pos)
        self._scope_mgr.add_instrn(whileloop)

    @add_position_arg
    def func(self, tree, pos):
        # args = [getSymValue(arg.children[0]) for arg in tree.children[1].children]
        treeArgList = tree.children[1].children
        argList = []
        for i in range(0, len(treeArgList), 2):
            argList.append(_get_sym_and_type(treeArgList[i:i+2], pos))


        sym = _get_sym(tree.children[0])
        rtn_type = _get_type(tree.children[2], pos)

        block = tree.children[3]
        # for arg in tree.children[1].children:
        #     args += [getSymValue(arg)]
        block = self._visit_get_instrs(block)

        # make sure we end with a Rtn
        if not block or not isinstance(block[-1], Rtn):
            block += [Rtn([], pos)]
        typed_sym = TypedSym(sym, rtn_type)
        func = Func(typed_sym, argList, block, pos)
        typed_func = TypedValue(func, rtn_type)
        # self._scope_mgr.add_func(typed_sym, typed_func, func)
        self._scope_mgr.init_symbol(typed_sym, typed_func, pos)

    @add_position_arg
    def func_call(self, tree, pos):
        sym = _get_sym(tree.children[0])
        callArgs = tree.children[1].children
        argInstrs = [self._visit_get_instrs(exprn) for exprn in callArgs]
        self._scope_mgr.add_instrn(Call(sym, argInstrs, pos))


    @add_position_arg
    def func_call_statement(self, tree, pos):
        self.visit_children(tree)
        self._scope_mgr.add_instrn(Pop(pos))

    @add_position_arg
    def rtn(self, tree, pos):
        exprn = []
        if len(tree.children):
            exprn = self._visit_get_instrs(tree.children[0])
        self._scope_mgr.add_instrn(Rtn(exprn, pos))