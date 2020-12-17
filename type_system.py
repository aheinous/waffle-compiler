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



class _TypeSysElem:
    def __str__(self):
        return str(self.__class__).split("'")[1].split('.')[-1]

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash( (self.__class__, 'I am an object') )


class Type(_TypeSysElem):
    @property
    def repr(self):
        return type_cpp_repr(self)


class Void(Type): pass

class _Num(Type): pass
class Int(_Num): pass
class Float(_Num): pass
class String(Type): pass
class Object(Type):
    def __init__(self, uid):
        self.uid = uid

    def __hash__(self):
        return hash(self.__class__, self.uid)




class _Op(_TypeSysElem):
    @property
    def repr(self):
        return op_cpp_repr(self)





class _BinOp(_Op): pass
class Add(_BinOp): pass
class Sub(_BinOp): pass
class Mul(_BinOp): pass
class Div(_BinOp): pass

class Eq(_BinOp): pass
class NotEq(_BinOp): pass
class Gt(_BinOp): pass
class GtEq(_BinOp): pass
class Lt(_BinOp): pass
class LtEq(_BinOp): pass

class And(_BinOp): pass
class Or(_BinOp): pass

class _UnaryOp(_Op): pass
class Neg(_UnaryOp): pass




# TODO make this a class

types_ = {
    'int': Int(),
    'float': Float(),
    'string': String(),
    'void': Void(),
}

def reg_new_type(sym, uid) -> Object:
    assert sym not in types_
    type_ = Object(uid)
    types_[sym] = type_
    return type_


def make_value(str_rep, type_, pos):
    value = match(type_,
        Int, lambda _ : MutableInt32(int(str_rep)),
        Float, lambda _: float(str_rep),
        String, lambda _: _decode_escapes(str_rep[1:-1])
    )
    return value

def make_type(str_rep, pos) -> Type :
    type_ = types_.get(str_rep, None)
    if type_ is None:
        raise UnrecognizedType(str_rep, pos)
    return type_



def value_cpp_repr(value, type_) :
    s = match(type_,
        _Num, lambda _ : str(value),
        String, lambda _:'"' + _encode_escapes(value) + '"'
    )
    return s

def type_cpp_repr(type_) -> str:
    return match(type_,
        Int, 'int',
        Float, 'float',
        String, 'std::string',
        Void, 'void'
    )

def op_cpp_repr(op) -> str:
    return match(op,
                Add,  '+',
                Sub,  '-',
                Mul,  '*',
                Div,  '/',
                Neg,  '-',
                Eq,   '=',
                NotEq,'!=',
                Gt,   '>',
                GtEq, '>=',
                Lt,   '<',
                LtEq, '<=',
                And,  '&&',
                Or,   '||',
                )

def check_assign_okay(l_type, r_type, pos):
    assert isinstance(l_type, Type)
    assert isinstance(r_type, Type)
    if not match( (l_type, r_type),
                        (_Num, _Num),       True,
                        (String, String),   True,
                        (Void, Void),       True,
                        (_,_),              lambda l_type, r_type: l_type == r_type):
        raise TypeMismatchException(l_type, r_type, pos)



def assign(l_type, r_type, r_value, pos):
    check_assign_okay(l_type, r_type, pos)

    return match( (l_type, r_type),
            (Int, _Num),    lambda a,b: r_value // 1,
            (Float, _Num),  lambda a,b: float(r_value),
            (_, _),         lambda a,b: r_value
    )



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

def unary_op_res_type(op, type_, pos):
    if not _unary_op_valid(op, type_):

        raise IllegalOperation('unary ' + op_cpp_repr(op) ,pos)
    return match(op,
            Neg, lambda _: type_)


def op_res_type(op, l_type, r_type, pos):
    ARITHMETIC = Union[Add, Sub, Mul, Div]
    COMPARE = Union[Eq, NotEq, Gt, GtEq, Lt, LtEq]
    BOOLEAN = Union[And, Or]

    res = match ((op, l_type, r_type),
            (ARITHMETIC, Int, Int),     Int(),
            (ARITHMETIC, _Num, _Num),   Float(),
            (COMPARE, Int, Int),        Int(),
            (BOOLEAN, _Num, _Num),      Int(),
            (Add, String, String),      String(),
            (_,_,_), None
    )
    if res is None:
        raise TypeMismatchException(l_type, r_type, pos)
    return res



def unary_op_res(op, value, type_, pos):
    res = match (op,
                    Neg, lambda _: -value)
    return res

def op_res(op, l_value, l_type, r_value, r_type, pos):


    res_type = op_res_type(op, l_type, r_type, pos)
    res = match (op,
                 Add,   lambda _: l_value + r_value,
                 Sub,   lambda _: l_value - r_value,
                 Mul,   lambda _: l_value * r_value,
                 Div,   lambda _: l_value / r_value,
                 Eq,    lambda _: l_value == r_value,
                 NotEq, lambda _: l_value != r_value,
                 Gt,    lambda _: l_value > r_value,
                 GtEq,  lambda _: l_value >= r_value,
                 Lt,    lambda _: l_value < r_value,
                 LtEq,  lambda _: l_value <= r_value,
                 And,   lambda _: l_value and r_value,
                 Or,    lambda _: l_value or r_value,
    )
    res = match(res_type,   Int, lambda _: MutableInt32(res//1),
                            Float, lambda  _: float(res),
                            _, lambda _ : res
                            )
    return res

# def main():
#     print(make_value('123', Int(), NoOne))
#     print(make_value('"Hello\\n"', String(), NoOne))

#     print(op_valid(Add(), Int(), Float()))
#     # print(op_valid('-', Int(), Float(), NoOne))
#     print(op_valid(Add(), String(), Float()))
#     print(op_valid(Add(), String(), String()))

#     print(op_res(Add(), make_value('10', Int(), NoOne), make_value('20', Int(), NoOne), NoOne))
#     print(op_res(Sub(), make_value('10', Int(), NoOne), make_value('20', Int(), NoOne), NoOne))
#     print(op_res(Mul(), make_value('10', Int(), NoOne), make_value('20', Int(), NoOne), NoOne))
#     print(op_res(Div(), make_value('25', Int(), NoOne), make_value('10', Int(), NoOne), NoOne))

#     print(op_res(Add(), make_value('20', Int(), NoOne), make_value('10.0', Float(), NoOne), NoOne))
#     # print(op_res(Add(), make_value('20', String(), NoOne), make_value('10.0', Float(), NoOne), NoOne))

#     print(cpp_repr(op_res(Add(), make_value('"20"', String(), NoOne), make_value('"10.0"', String(), NoOne), NoOne)))
#     print(cpp_repr(op_res(Add(), make_value('"\tHello "', String(), NoOne), make_value('"World\n"', String(), NoOne), NoOne)))
#     print(make_value('"\tHello"', String(), NoOne))


# if __name__ == '__main__':
#     main()


