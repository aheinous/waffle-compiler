
from lark.exceptions import LarkError, UnexpectedEOF


class RtnException(Exception):
    pass



class LarkErrorWithPos(LarkError):
    def __init__(self, lark_error, pos):
        self.lark_error = lark_error
        self.pos = pos


# TODO print file context  properl;y



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
    def __init__(self,  sym, pos):
        super().__init__("Symbol reassignment: \"{}\"".format(sym), pos)

class SymbolNotFound(VMRuntimeException):
    def __init__(self,  sym, pos):
        super().__init__('Symbol not found: "' + sym +'"', pos)

class UnrecognizedType(VMRuntimeException):
    def __init__(self, str_rep, pos):
        super().__init__("Unrecognized type: " + str_rep, pos)

class IllegalOperation(VMRuntimeException):
    def __init__(self,  op, pos):
        super().__init__("The {} operation is illegal in this context.".format(op), pos)

class ReadUninitializedValue(VMRuntimeException):
    def __init__(self,  sym, pos):
        super().__init__('Reading uninitialized value: "' + sym +'"', pos)
        self.sym = sym

class MixinException(VMRuntimeException):
    def __init__(self, sym, pos):
        self.sym = sym
        super().__init__('The symbol {} is unknowable at compile time.'.format(sym), pos)

