from position import Position
from instruction_block import Block
from typed_data import RValue, TSym



class Func:
    def __init__(self, typed_sym, args, instrns, pos):
        assert isinstance(typed_sym, TSym)
        self.typed_sym = typed_sym
        self.args = args
        self.instrns = instrns
        self.pos = pos

    @property
    def rtn_type(self):
        return self.typed_sym.type



class Instrn:
    def __init__(self, pos):
        self.pos = pos
        self.child_scopes = {}

    def _add_child_scope(self, name, child_scope):
        self.child_scopes[name] = child_scope


    def __repr__(self):
        s = self.__class__.__name__ + ' '
        # for k,v in vars(self).items():
        #     s += '{} {},'.format(k,v)
        return '(' + s + str(self.pos) + ')'


class BinOp(Instrn):
    def __init__(self, op, pos):
        super().__init__(pos)
        self.op = op



class UnaryOp(Instrn):
    def __init__(self, op, pos):
        super().__init__(pos)
        self.op = op


class Assign(Instrn):
    def __init__(self, pos):
        super().__init__(pos)



class Decl(Instrn):
    def __init__(self, typed_sym, pos):
        super().__init__(pos)
        assert isinstance(typed_sym, TSym)
        self.typed_sym = typed_sym



class Pushi(Instrn):
    def __init__(self, value, pos):
        super().__init__(pos)
        assert isinstance(value, RValue)
        self.value = value



class Push(Instrn):
    def __init__(self, sym, pos):
        super().__init__(pos)
        self.sym = sym



class InitFunc(Instrn):
    def __init__(self, typed_sym, typed_func, pos):
        super().__init__(pos)
        self.typed_sym = typed_sym
        self.typed_func = typed_func
        self._add_child_scope('func_blk', typed_func.value().instrns)




class Call(Instrn):
    def __init__(self, func_sym, arg_exprns, pos):
        super().__init__(pos)
        self.func_sym = func_sym
        self.arg_exprns = arg_exprns


class Rtn(Instrn):
    def __init__(self, exprn, pos):
        super().__init__(pos)
        self.exprn = exprn


class Pop(Instrn):
    pass

class IfElse(Instrn):
    def __init__(self, condBlk, ifBlk, elseBlk, pos):
        super().__init__(pos)
        self.condBlk = condBlk
        self._add_child_scope('if_blk', ifBlk)
        self._add_child_scope('else_blk', elseBlk)

        self.ifBlk = ifBlk
        self.elseBlk = elseBlk



class WhileLoop(Instrn):
    def __init__(self, condBlk, loop, pos):
        super().__init__(pos)
        self.condBlk = condBlk
        self.loop = loop

        self._add_child_scope('loop', loop)


class Mixin(Instrn):
    def __init__(self, exprn, pos):
        super().__init__(pos)
        self.exprn = exprn

class MixinStatements(Instrn):
    def __init__(self, statements, pos):
        super().__init__(pos)
        self.statements = statements


class ClassDecl(Instrn):
    def __init__(   self, t_sym:TSym,
                    contents:Block,
                    t_init_func:RValue,
                    pos:Position):
        super().__init__(pos)
        self.t_sym = t_sym
        contents.persistent_scope = True
        self.contents = contents
        self.t_init_func = t_init_func
        self._add_child_scope('contents', contents)

class ObjectInit(Instrn):
    def __init__(self, type_, pos:Position):
        super().__init__(pos)
        self.type = type_