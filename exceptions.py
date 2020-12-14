
from lark.exceptions import LarkError, UnexpectedEOF


class RtnException(Exception):
    pass



class LarkErrorWithPos(LarkError):
    def __init__(self, lark_error, pos):
        self.lark_error = lark_error
        self.pos = pos




class VMRuntimeException(Exception):
    def __init__(self, desc, pos):
        super().__init__(desc)
        self.pos = pos

    def __str__(self):
        s = super().__str__()
        s += '\nAt ' + str(self.pos)
        return s

class TypeMismatchException(VMRuntimeException):
    def __init__(self, typeLeft, typeRight, pos):
        super().__init__('Type mismatch: {} {}'.format(typeLeft, typeRight), pos)

class SymbolReassignment(VMRuntimeException):
    def __init__(self,  pos):
        super().__init__("Symbol reassignment", pos)

class SymbolNotFound(VMRuntimeException):
    def __init__(self,  pos):
        super().__init__("Assignment to undeclared variable", pos)

class UnrecognizedType(VMRuntimeException):
    def __init__(self,  pos):
        super().__init__("Unrecognized type", pos)

class IllegalOperation(VMRuntimeException):
    def __init__(self,  pos):
        super().__init__("Illegal Operation", pos)
