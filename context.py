from instruction_tree_visitor import InstrnTreeVisitor
import unittest
from exceptions import SymbolNotFound, SymbolReassignment
from type_system import (   check_assign_okay as type_sys_verify_assign,
                            assign as type_sys_assign
                            )


VALUE = 'VALUE'
TYPE = 'TYPE'


class SymbolTable:
    def __init__(self):
        self._tbl = {}

    def insert(self, sym, field, value):
        if sym not in self._tbl:
            self._tbl[sym] = {}
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
        self.name = ''
        self.uid = None
        self.instance_uid = None
        self.symbol_tbl = SymbolTable()
        self.persists = False
        self.parent = None
        self.symbol_values = {}
        self.children = []
        self.tmp_cnt = 0


    def insert(self, sym, field, value):
        if sym not in self.symbol_tbl:
            # must init all symbols with type value first
            assert field == TYPE

        if field == VALUE:
            assert self.read(sym, TYPE) == value.type
            self.symbol_values[sym] = value
            return

        self.symbol_tbl.insert(sym, field, value)


    def read(self, sym, field):
        if field == VALUE:
            return self.symbol_values[sym]
        return self.symbol_tbl.read(sym, field)

    def has_field(self,sym, field):
        if field == VALUE:
            return sym in self.symbol_values
        return sym in self.symbol_tbl

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
        indent_str = self.indent*4*' '
        print('{}name: {}, uid: {}'.format(indent_str, scope.name, scope.uid))
        print('{}{}'.format(indent_str,scope.symbol_values))
        self.indent += 1
        self.visit_children(scope)
        self.indent -= 1

class ScopeMaker(InstrnTreeVisitor):

    def __init__(self):
        super().__init__()
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

    def visit_new_scope(self, name, instrns):
        if not instrns:
            return
        self._push(name, instrns.uid, instrns)
        self.visit_blk(instrns)
        self._pop()

class RAII_Scope:
    def __init__(self, ctx):
        self._ctx = ctx

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ctx._exit_scope()

class Context:
    def __init__(self):
        self._scopes_by_uid = {}
        self._cur_scope = None
        self._scope_history = []
        self._root = None


    def add_new_scopes(self, scope_list):
        for scope in scope_list:
            assert scope.uid not in self._scopes_by_uid
            self._scopes_by_uid[scope.uid] = scope
            if not scope.parent:
                assert self._root is None
                self._root = scope

    def enter_scope(self, uid, instanceid = None):
        self._scope_history.append(self._cur_scope)
        self._cur_scope = self._scopes_by_uid[uid]
        return RAII_Scope(self)


    def _exit_scope(self):
        self._cur_scope.symbol_values = {}
        self._cur_scope = self._scope_history.pop()

    def init_symbol(self, typed_sym, typed_value, pos):
        self.declare_symbol(typed_sym, pos)
        self.assign_symbol(typed_sym.sym, typed_value, pos)

    def declare_symbol(self, typed_sym, pos):
        sym = typed_sym.sym
        type_ = typed_sym.type
        if sym in self._cur_scope \
            and self._cur_scope.has_field(sym,VALUE):
            raise SymbolReassignment(pos)
        self._cur_scope.insert(sym, TYPE, type_)


    def _scope_hierarchy(self):
        scope = self._cur_scope
        while True:
            yield scope
            if not scope.parent:
                break
            scope = scope.parent

    def assign_symbol(self, sym, typed_value, pos):
        for scope in self._scope_hierarchy():
            if sym in scope:
                new_value = type_sys_assign(scope.read(sym, TYPE), typed_value, pos)
                scope.insert(sym, VALUE, new_value)
                return
        raise SymbolNotFound(pos)


    def check_assign_okay(self, sym, something_typed, pos):
        for scope in self._scope_hierarchy():
            if sym in scope:
                type_sys_verify_assign(scope.read(sym, TYPE), something_typed.type, pos)
                return
        raise SymbolNotFound(pos)


    def read(self, sym, field, pos):
        for scope in self._scope_hierarchy():
            if sym in scope:
                return scope.read(sym, field)
        raise SymbolNotFound(pos)

    def next_tmp(self):
        self._cur_scope.tmp_cnt += 1
        return self._cur_scope.tmp_cnt - 1

    def __contains__(self, sym):
        for scope in self._scope_hierarchy():
            if sym in scope:
                return True
        return False

if __name__ == '__main__':
    unittest.main()
