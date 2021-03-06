from type_system import typeSystem
import type_system as type_sys
import context

class _Typed:
    @property
    def type_repr(self):
        return typeSystem.type_cpp_repr(self.type)

    def checkCanAssignTo(self, type_,  pos):
        typeSystem.check_assign_okay(self.type, type_, pos)

    def checkAssignOkay(self, other, pos):
        typeSystem.check_assign_okay(self.type, other.type, pos)

    def opResType(self, op, other, pos):
        return typeSystem.op_res_type(op, self.type, other.type, pos)

def typeFromString(string, pos):
    return typeSystem.make_type(string, pos)

def regNewType(strRep, type_):
    return typeSystem.reg_new_type(strRep, type_)


class RValue(_Typed):
    def __init__(self, value, type):
        self.type = type
        self._value = value
        assert isinstance(self.type, type_sys.Type)
        assert not isinstance(self._value, RValue)

    def __repr__(self):
        s = '(RValue {} {})'.format(self._value, self.type)
        return s

    @property
    def repr(self):
        return typeSystem.value_cpp_repr(self._value, self.type)

    @staticmethod
    def fromString(string, type_, pos):
        return RValue(typeSystem.make_value(string, type_, pos), type_)

    def binOpRes(self, op, other, ctx, pos):
        other = other.rvalue(ctx, pos)
        resValue = typeSystem.op_res( op,
                                    self._value, self.type,
                                    other._value, other.type, pos)
        resType = typeSystem.op_res_type(op, self.type, other.type, pos)
        return RValue(resValue, resType)

    def unaryOpRes(self, op, ctx, pos):
        resValue = typeSystem.unary_op_res(op, self.value(), self.type, pos)
        resType = typeSystem.unary_op_res_type(op, self.type, pos)
        return RValue(resValue, resType)

    def value(self, ctx=None, pos=None):
        return self._value

    def rvalue(self, ctx, pos):
        return self

    def tfrag(self, ctx=None, pos=None):
        return TFrag(self.repr, self.type)



class TSym(_Typed):
    def __init__(self, sym, type):
        self.sym = sym
        self.type = type
        assert isinstance(self.type, type_sys.Type)
        assert isinstance(self.sym, str)

    def __repr__(self):
        s = '(TSym {} {})'.format(self.sym, self.type)
        return s

    @property
    def string(self):
        return self.sym


class LValue(_Typed):
    def __init__(self, sym, type_, scope_uid):
        self.sym = sym
        self.type = type_
        self.scope_uid = scope_uid
        assert not isinstance(self.type, _Typed)

    def assign(self, t_value, ctx, pos):
        rvalue = t_value.rvalue(ctx, pos)
        newValue_untyped = typeSystem.assign(self.type, rvalue.type, rvalue.value(), pos)
        rvalue = RValue(newValue_untyped, self.type)
        ctx.assign_value_at(self.scope_uid, self.sym, rvalue, pos)

    def rvalue(self, ctx, pos):
        rvalue = ctx.read_from_scope(self.sym, self.scope_uid, context.VALUE, pos)
        return rvalue

    def value(self, ctx, pos):
        return self.rvalue(ctx, pos).value()


    def binOpRes(self, op, other, ctx, pos):
        other = other.rvalue(ctx, pos)
        return self.rvalue(ctx, pos).binOpRes(op, other, ctx, pos)

    def unaryOpRes(self, op, ctx, pos):
        return self.rvalue(ctx, pos).unaryOpRes(op, ctx, pos)


    def tfrag(self, ctx, pos):
        return self.rvalue(ctx, pos).tfrag()



    # TODO scope?
    @property
    def string(self):
        return self.sym


class TFrag(_Typed):
    def __init__(self, fragment, type):
        self.fragment = fragment
        self.type = type
        assert isinstance(self.type, type_sys.Type)
        assert isinstance(self.fragment, str)


    @property
    def repr(self):
        return self.fragment


    def __repr__(self):
        s = '(TFrag {} {})'.format(self.fragment, self.type)
        return s


    def unaryOpRes(self, op, ctx, pos):
        resType = typeSystem.unary_op_res_type(op, self.type, pos)
        resRepr = '{}{}'.format(typeSystem.op_cpp_repr(op), self.fragment)
        return TFrag(resRepr, resType)