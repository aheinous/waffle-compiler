from pampy import match, _
from fixedint import *
from exceptions import IllegalOperation, TypeMismatchException, UnrecognizedType
import re
import codecs

from typing import Union


_ESCAPE_SEQUENCE_RE = re.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', re.UNICODE | re.VERBOSE)

def _decode_escapes(s):
    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return _ESCAPE_SEQUENCE_RE.sub(decode_match, s)


def _encode_escapes(s):
    return s.translate(str.maketrans({
        '\n':'\\n',
        '\r':'\\r',
        '\f': '\f',
        '\t':'\\t',
        '\'': '\\\'',
        '\"': '\\\"',
        '?':'\\?',
        '\\': '\\\\'
    }))




class _Type:
    @property
    def repr(self):
        return type_cpp_repr(self)


class Void(_Type): pass

class _Num(_Type): pass
class Int(_Num): pass
class Float(_Num): pass
class String(_Type): pass


class _Op:
    @property
    def repr(self):
        return op_cpp_repr(self)


class _BinOp(_Op): pass
class Add(_BinOp): pass
class Sub(_BinOp): pass
class Mul(_BinOp): pass
class Div(_BinOp): pass
class _UnaryOp(_Op): pass
class Neg(_UnaryOp): pass


class _Typed:
    @property
    def type_repr(self):
        return type_cpp_repr(self.type)

class TypedValue(_Typed):
    def __init__(self, value, type):
        self.type = type
        self.value = value
        assert isinstance(self.type, _Type)
        assert not isinstance(self.value, TypedValue)

    def __repr__(self):
        s = '(TypedValue {} {})'.format(self.value, self.type)
        return s

    @property
    def cpp_repr(self):
        return cpp_repr(self)


class TypedSym(_Typed):
    def __init__(self, sym, type):
        self.sym = sym
        self.type = type
        assert isinstance(self.type, _Type)
        assert isinstance(self.sym, str)

    def __repr__(self):
        s = '(TypedSym {} {})'.format(self.sym, self.type)
        return s

    @property
    def string(self):
        return self.sym



class TypedStr(_Typed):
    def __init__(self, string, type):
        self.string = string
        self.type = type
        assert isinstance(self.type, _Type)
        assert isinstance(self.string, str)

    def __repr__(self):
        s = '(TypedStr {} {})'.format(self.string, self.type)
        return s



class TypedSymValue(TypedValue):
    def __init__(self, *args):
        if len(args) == 2:
            self.sym = args[0]
            self.value = args[1].value
            self.value = args[1].type
        elif len(args) == 3:
            self.sym = args[0]
            self.value = args[1]
            self. type = args[2]
        assert isinstance(self.type, _Type)

    @property
    def typed_value(self):
        return TypedValue(self.value, self.type)


def make_value(str_rep, type_, pos) -> TypedValue :
    value = match(type_,
        Int, lambda _ : MutableInt32(int(str_rep)),
        Float, lambda _: float(str_rep),
        String, lambda _: _decode_escapes(str_rep[1:-1])
    )
    return TypedValue(value, type_)

def make_type(str_rep, pos) -> _Type :
    type_ = match( str_rep,
                    'int', Int(),
                    'float', Float(),
                    'string', String(),
                    'void', Void(),
                    _, None
    )
    if type_ is None:
        raise UnrecognizedType(pos)
    return type_



def cpp_repr(typed_value) -> TypedStr :
    v = typed_value.value
    s = match(typed_value.type,
        _Num, lambda _ : str(v),
        String, lambda _:'"' + _encode_escapes(v) + '"'
    )
    return TypedStr(s, typed_value.type)

def type_cpp_repr(type_) -> str:
    return match(type_,
        Int, 'int',
        Float, 'float',
        String, 'std::string',
        Void, 'void'
    )

def op_cpp_repr(op) -> str:
    return match(op,
                Add, '+',
                Sub, '-',
                Mul, '*',
                Div, '/',
                Neg, '-'
                )

def check_assign_okay(l_type, r_type, pos):
    assert isinstance(l_type, _Type)
    assert isinstance(r_type, _Type)
    if not match( (l_type, r_type),
            (_Num, _Num), True,
            (String, String), True,
            (Void, Void), True,
            _, False):
        raise TypeMismatchException(l_type, r_type, pos)



def assign(l_type, right, pos):
    r_type = right.type
    check_assign_okay(l_type, r_type, pos)
    value = right.value


    # TODO
    # hack for 'if instanceof(value, Func)'
    if 'instructions.Func' in str(value.__class__):
        return TypedValue(value, l_type)


    return TypedValue(match( (l_type, r_type),
            (Int, _Num), lambda a,b: value // 1,
            (Float, _Num), lambda a,b: float(value),
            (String, String), lambda a,b: value
    ), l_type)


def _unary_op_valid(op, type_):
    return match(op,
                Neg, lambda _: match(type_, _Num, True,
                                            _,   False),
                _, False)

def op_valid(op, l_type, r_type=None):
    if r_type is None:
        return _unary_op_valid(op, l_type)

    return match( [l_type, r_type],
        (_Num, _Num), lambda a,b: match(op,   Union[Add, Sub, Mul, Div], True,
                                            _, False
                                            ),
        (String, String), lambda a,b: match(op, Add, True,
                                                _, False
                                                ),
        _, False
    )

def _unary_op_res_type(op, type_, pos):
    if not _unary_op_valid(op, type_):
        raise IllegalOperation(pos)
    return match(op,
            Neg, lambda _: type_)


def op_res_type(op, *args):
    if len(args) == 2:
        return _unary_op_res_type(op, *args)
    l_type, r_type, pos = args


    res = match ((l_type, r_type),
            (Int, Int),         lambda a,b: match(op,   Union[Add, Sub, Mul, Div], Int(),
                                                    _, None),
            (Float, Float),     lambda a,b: match(op, Union[Add, Sub, Mul, Div], Float(),
                                                    _, None),
            (Float, Int),       lambda a,b: match(op,   Union[Add, Sub, Mul, Div], Float(),
                                                    _, None),
            (Int, Float),       lambda a,b: match(op,   Union[Add, Sub, Mul, Div], Float(),
                                                    _, None),
            (String, String),   lambda a,b: match(op, Add, String(),
                                                    _, None),
            (_,_), None
    )
    if res is None:
        raise TypeMismatchException(l_type, r_type, pos)
    return res

def _unary_op_res(op, typed_value, pos):
    res_type = _unary_op_res_type(op, typed_value.type, pos)
    res = match (op,
                Neg, lambda _: -typed_value.value)
    return TypedValue(res, res_type)

def op_res(*args) -> TypedValue:
    if len(args) == 3:
        return _unary_op_res(*args)
    op, l_typed_value, r_typed_value, pos = args
    l_type,  r_type  = l_typed_value.type,  r_typed_value.type
    l_value, r_value = l_typed_value.value, r_typed_value.value
    res_type = op_res_type(op, l_type, r_type, pos)
    res = match (op,
                 Add, lambda _: l_value + r_value,
                 Sub, lambda _: l_value - r_value,
                 Mul, lambda _: l_value * r_value,
                 Div, lambda _: l_value / r_value
    )
    res = match(res_type,   Int, lambda _: MutableInt32(res//1),
                            Float, lambda  _: float(res),
                            _, lambda _ : res
                            )
    return TypedValue(res, res_type)

def main():
    print(make_value('123', Int(), NoOne))
    print(make_value('"Hello\\n"', String(), NoOne))

    print(op_valid(Add(), Int(), Float()))
    # print(op_valid('-', Int(), Float(), NoOne))
    print(op_valid(Add(), String(), Float()))
    print(op_valid(Add(), String(), String()))

    print(op_res(Add(), make_value('10', Int(), NoOne), make_value('20', Int(), NoOne), NoOne))
    print(op_res(Sub(), make_value('10', Int(), NoOne), make_value('20', Int(), NoOne), NoOne))
    print(op_res(Mul(), make_value('10', Int(), NoOne), make_value('20', Int(), NoOne), NoOne))
    print(op_res(Div(), make_value('25', Int(), NoOne), make_value('10', Int(), NoOne), NoOne))

    print(op_res(Add(), make_value('20', Int(), NoOne), make_value('10.0', Float(), NoOne), NoOne))
    # print(op_res(Add(), make_value('20', String(), NoOne), make_value('10.0', Float(), NoOne), NoOne))

    print(cpp_repr(op_res(Add(), make_value('"20"', String(), NoOne), make_value('"10.0"', String(), NoOne), NoOne)))
    print(cpp_repr(op_res(Add(), make_value('"\tHello "', String(), NoOne), make_value('"World\n"', String(), NoOne), NoOne)))
    print(make_value('"\tHello"', String(), NoOne))


if __name__ == '__main__':
    main()


