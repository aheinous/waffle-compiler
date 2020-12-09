from exceptions import SymbolNotFound, SymbolReassignment
from type_checking import Void, TypedValue, TypedSym, check_types_for_assign


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

    def init_symbol(self, typed_sym, typed_value, who):
        self.declare_symbol(typed_sym, who)
        self.assign_symbol(typed_sym.name, typed_value, who)

    def declare_symbol(self, typed_sym, who):
        if typed_sym.name in self:
            raise SymbolReassignment(who.pos)
        self._cur_scope.symbols[typed_sym.name] = TypedValue(Void, typed_sym.type)


    def assign_symbol(self, sym, typed_value, who):
        for scope in reversed(self._scope_stack):
            if sym in scope.symbols:
                check_types_for_assign(scope.symbols[sym], typed_value, who)
                scope.symbols[sym] = TypedValue(typed_value.value, scope.symbols[sym].type)
                return
        raise SymbolNotFound(who.pos)

    def verify_assign(self, sym, something_typed, who):
        for scope in reversed(self._scope_stack):
            if sym in scope.symbols:
                check_types_for_assign(scope.symbols[sym], something_typed, who)
                return
        raise SymbolNotFound(who.pos)

    def read_symbol(self, sym, who) -> TypedValue:
        for scope in reversed(self._scope_stack):
            if sym in scope.symbols:
                return scope.symbols[sym]
        raise SymbolNotFound(who.pos)


    # def get_symbol_type(self, sym, who):
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
