from instruction_tree_visitor import InstrnTreeVisitor
import unittest
from exceptions import SymbolNotFound, SymbolReassignment
from type_system import (   TypedValue,
                            check_assign_okay as type_sys_verify_assign,
                            assign as type_sys_assign
                            )
from enum import IntEnum, auto


VALUE = 0
TYPE = 1

class SymbolTable:
    def __init__(self):
        self._tbl = {}

    def insert(self, sym, field, value):
        if sym not in self._tbl:
            self._tbl[sym] = {}
        assert field not in self._tbl[sym]
        self._tbl[sym][field] = value

    def read(self, sym, field):
        return self._tbl[sym][field]

    def __contains__(self, sym):
        return sym in self._tbl


class TestSymbolTable(unittest.TestCase):
    def test_insertGet(self):
        tbl = SymbolTable()
        tbl.insert('a', 'f', 3)
        self.assertEqual(tbl.read('a', 'f'), 3)

        self.assertRaises(AssertionError, lambda: tbl.insert('a', 'f', 3))
        tbl.insert('a', 'g', 3)

        self.assertTrue('a' in tbl)
        self.assertFalse('b' in tbl)

class _Scope:
    def __init__(self):
        '''
        uid
        symbol_tbl
        persists:Bool
        parent
        instanceVars
        '''
        self.name = ''
        self.uid = None
        self.instance_uid = None
        self.symbol_tbl = SymbolTable()
        self.persists = False
        self.parent = None
        self.symbol_values = {}
        self.children = []
        self.tmp_cnt = 0

    # def typed_value(self, sym):
    #     return TypedValue(self.symbol_values[sym], self.symbol_tbl.read(sym, TYPE))

    def insert(self, sym, field, value):
        if field == VALUE:
            assert(sym in self.symbol_tbl)
            assert self.read(sym, TYPE) == value.type
            self.symbol_values[sym] = value
            return
        self.symbol_tbl.insert(sym, field, value)
        if field == TYPE:
            assert sym not in self.symbol_values
            self.symbol_values[sym] = TypedValue(None, value)

    def read(self, sym, field):
        if field == VALUE:
            return self.symbol_values[sym]
        return self.symbol_tbl.read(sym, field)

    def __contains__(self, sym):
        return sym in self.symbol_tbl

class ScopeTreeVisitor:

    def visit(self, scope):
        self.visit_children(scope)

    def visit_children(self, scope):
        for child in scope.children:
            self.visit(child.name, child)

class ScopeTreePrinter(ScopeTreeVisitor):
    def __init__(self):
        self.indent = 0

    def visit(self, name, scope):
        print('{}name: {}, uid: {}'.format(self.indent*4*' ', scope.name, scope.uid))
        print(scope.symbol_values)
        self.indent += 1
        self.visit_children(scope)
        self.indent -= 1

class ScopeMaker(InstrnTreeVisitor):

    def __init__(self):
        self._stack = []
        self._scopes = []

    def _push(self, name, uid, persists=False):
        new_scope = _Scope()
        new_scope.name = name
        new_scope.uid = uid
        new_scope.persists = persists
        if self._stack:
            new_scope.parent = self._stack[-1]
            self._stack[-1].children.append(new_scope)
        self._stack.append(new_scope)
        self._scopes.append(new_scope)

    def _pop(self):
        self._stack.pop()

    @property
    def scopes(self) -> list :
        return self._scopes

    def on_visit_new_scope(self, name, instrns):
        if not instrns:
            return
        self._push(name, instrns[0].pos, instrns)
        self.visit(instrns)
        self._pop()

class Context:
    def __init__(self):
        self._scopes_by_uid = {}
        self._cur_scope = None


    def add_new_scopes(self, scope_list):
        for scope in scope_list:
            assert scope.uid not in self._scopes_by_uid
            self._scopes_by_uid[scope.uid] = scope

    def enter_scope(self, uid, instanceid = None):
        self._cur_scope = self._scopes_by_uid[uid]

    def exit_scope(self, uid):
        self._cur_scope.symbol_values = {}

    def init_symbol(self, typed_sym, typed_value, pos):
        self.declare_symbol(typed_sym, pos)
        self.assign_symbol(typed_sym.sym, typed_value, pos)

    def declare_symbol(self, typed_sym, pos):
        if typed_sym.sym in self._cur_scope:
            raise SymbolReassignment(pos)
        self._cur_scope.insert(typed_sym.sym, TYPE, typed_sym.type)
        # self.cur_scope.symbol_values[typed_sym.sym] = None


    def _scope_hierarchy(self):
        scope = self._cur_scope
        while True:
            yield scope
            if not scope.parent:
                break
            scope = scope.parent

    def assign_symbol(self, sym, typed_value, pos):
        print('assign {} {}'.format(sym, typed_value))
        for scope in self._scope_hierarchy():
            if sym in scope:
                new_value = type_sys_assign(scope.read(sym, VALUE), typed_value, pos)
                scope.insert(sym, VALUE, new_value)
                return
        raise SymbolNotFound(pos)


    def check_assign_okay(self, sym, something_typed, pos):
        for scope in self._scope_hierarchy():
            if sym in scope:
                type_sys_verify_assign(scope.read(sym, TYPE), something_typed.type, pos)
                return
        raise SymbolNotFound(pos)

    def read_symbol(self, sym, pos) -> TypedValue:
        for scope in self._scope_hierarchy():
            if sym in scope:
                return scope.read(sym, VALUE)
        raise SymbolNotFound(pos)

    # def add_instrn(self, instrn):
    #     self.cur_scope.instrns.append(instrn)

    def __contains__(self, sym):
        for scope in self._scope_hierarchy():
            if sym in scope:
                return True
        return False


# def unittests():


if __name__ == '__main__':
    # unittest()
    unittest.main()

    # def init_symbol(self, typed_sym, typed_value, pos):
    #     self.declare_symbol(typed_sym, pos)
    #     self.assign_symbol(typed_sym.sym, typed_value, pos)

    # def declare_symbol(self, typed_sym, pos):
    #     if typed_sym.sym in self.cur_scope.symbols:
    #         raise SymbolReassignment(pos)
    #     self.cur_scope.symbols[typed_sym.sym] = TypedValue(None, typed_sym.type)


    # def assign_symbol(self, sym, typed_value, pos):
    #     for scope in reversed(self._scope_stack):
    #         if sym in scope.symbols:
    #             new_value = type_sys_assign(scope.symbols[sym], typed_value, pos)
    #             scope.symbols[sym] = new_value
    #             return
    #     raise SymbolNotFound(pos)

    # def check_assign_okay(self, sym, something_typed, pos):
    #     for scope in reversed(self._scope_stack):
    #         if sym in scope.symbols:
    #             type_sys_verify_assign(scope.symbols[sym].type, something_typed.type, pos)
    #             return
    #     raise SymbolNotFound(pos)

    # def read_symbol(self, sym, pos) -> TypedValue:
    #     for scope in reversed(self._scope_stack):
    #         if sym in scope.symbols:
    #             return scope.symbols[sym]
    #     raise SymbolNotFound(pos)