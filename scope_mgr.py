from exceptions import SymbolNotFound, SymbolReassignment
# from type_checking import Void, TypedValue, TypedSym, check_types_for_assign
from type_system import TypedValue, TypedSym, verify_assign as type_sys_verify_assign, assign as type_sys_assign

class _Scope:
    def __init__(self) -> None:
        self.instrns = []
        self.symbols = {} # {str : TypedValue }
        self.func = None


class ScopeMgr:
    def __init__(self):
        self._scope_stack = [_Scope()]
        self._func_stack = []

    def push_func_scope(self, func):
        self.push_scope()
        self._cur_scope.func = func
        self._func_stack.append(func)

    def push_scope(self):
        self._scope_stack.append(_Scope())

    def pop_scope(self):
        old_scope = self._scope_stack.pop()
        if old_scope.func and old_scope.func is self.func:
            self._func_stack.pop()

    @property
    def func(self):
        if not self._func_stack:
            return None
        return self._func_stack[-1]

    @property
    def _cur_scope(self):
        return self._scope_stack[-1]

    def init_symbol(self, typed_sym, typed_value, pos):
        self.declare_symbol(typed_sym, pos)
        self.assign_symbol(typed_sym.sym, typed_value, pos)

    def declare_symbol(self, typed_sym, pos):
        if typed_sym.sym in self._cur_scope.symbols:
            raise SymbolReassignment(pos)
        self._cur_scope.symbols[typed_sym.sym] = TypedValue(None, typed_sym.type)


    def assign_symbol(self, sym, typed_value, pos):
        for scope in reversed(self._scope_stack):
            if sym in scope.symbols:
                # check_types_for_assign(scope.symbols[sym], typed_value, pos)
                new_value = type_sys_assign(scope.symbols[sym], typed_value, pos)
                # scope.symbols[sym] = TypedValue(typed_value.value, scope.symbols[sym].type)
                scope.symbols[sym] = new_value
                return
        raise SymbolNotFound(pos)

    def verify_assign(self, sym, something_typed, pos):
        for scope in reversed(self._scope_stack):
            if sym in scope.symbols:
                type_sys_verify_assign(scope.symbols[sym].type, something_typed.type, pos)
                return
        raise SymbolNotFound(pos)

    def read_symbol(self, sym, pos) -> TypedValue:
        for scope in reversed(self._scope_stack):
            if sym in scope.symbols:
                return scope.symbols[sym]
        raise SymbolNotFound(pos)


    # def get_symbol_type(self, sym, pos):
    #     for scope in reversed(self._scope_stack):
    #         if sym in scope.symbols:

    def add_instrn(self, instrn):
        self._cur_scope.instrns.append(instrn)

    def __contains__(self, sym):
        for scope in reversed(self._scope_stack):
            if sym in scope.symbols:
                return True
        return False

    @property
    def instrns(self):
        return self._cur_scope.instrns


    @property
    def global_symbols(self):
        return self._scope_stack[0].symbols
