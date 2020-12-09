from collections import namedtuple
from exceptions import TypeMismatchException

class VoidType:
    def __eq__(self, o: object) -> bool:
        return isinstance(o, VoidType)

    def __str__(self):
        return "Void"


Void = VoidType()

# _TypedValue = namedtuple('TypedValue', ['value', 'type'])
# _TypedSym = namedtuple('TypedSym', ['name', 'type'])

def _check_types(func):
    def _check_types_wrapper(self, other, who):
        if self.type != other.type:
            raise TypeMismatchException(self.type, other.type, who.pos)
        return func(self, other)
    return _check_types_wrapper


class TypedValue():
    def __init__(self, value, type):
        self.type = type
        self.value = value

        assert(isinstance(self.type, str))

    def __repr__(self):
        return '(TypedValue {} {})'.format(self.value, self.type)

    def neg(self, who):
        return TypedValue(-self.value, self.type)

    @_check_types
    def lt(self, other):
        return TypedValue(self.value < other.value, self.type)

    @_check_types
    def le(self, other):
        return TypedValue(self.value <= other.value, self.type)

    @_check_types
    def eq(self, other):
        return TypedValue(self.value == other.value, self.type)

    @_check_types
    def ne(self, other):
        return TypedValue(self.value != other.value, self.type)

    @_check_types
    def gt(self, other):
        return TypedValue(self.value > other.value, self.type)

    @_check_types
    def ge(self, other):
        return TypedValue(self.value >= other.value, self.type)

    @_check_types
    def add(self, other):
        return TypedValue(self.value + other.value, self.type)

    @_check_types
    def sub(self, other):
        return TypedValue(self.value - other.value, self.type)

    @_check_types
    def mul(self, other):
        return TypedValue(self.value * other.value, self.type)

    @_check_types
    def matmul(self, other):
        return NotImplemented

    @_check_types
    def div(self, other):
        if self.type == 'int':
            return TypedValue(self.value // other.value, self.type)
        return TypedValue(self.value / other.value, self.type)


    # @_check_types
    # def floordiv(self, other):
    #     return TypedValue(self.value // other.value, self.type)

    @_check_types
    def mod(self, other):
        return TypedValue(self.value % other.value, self.type)

    @_check_types
    def divmod(self, other):
        return NotImplemented

    @_check_types
    def pow(self, other, modulo=None):
        return NotImplemented

    @_check_types
    def lshift(self, other):
        return TypedValue(self.value << other.value, self.type)

    @_check_types
    def rshift(self, other):
        return TypedValue(self.value >> other.value, self.type)

    @_check_types
    def and_(self, other):
        return TypedValue(self.value & other.value, self.type)

    @_check_types
    def xor(self, other):
        return TypedValue(self.value ^ other.value, self.type)

    @_check_types
    def or_(self, other):
        return TypedValue(self.value | other.value, self.type)




class TypedSym:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        assert(isinstance(self.type, str))

    def __repr__(self):
        return '(TypedSym {} {})'.format(self.value, self.type)

    @property
    def value(self):
        return self.name

def assert_typed(x):
    assert isinstance(x, TypedValue) or isinstance(x, TypedSym)

def check_types_for_assign(left, right, who):
    if left.type != right.type:
        raise TypeMismatchException(left.type, right.type, who.pos)