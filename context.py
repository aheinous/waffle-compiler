import unittest
from exceptions import SymbolNotFound, SymbolReassignment

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

    def __str__(self):
        l = []
        for sym, field_dict in self._tbl.items():
            l.append('{}: {}'.format(sym, field_dict))
        return '\n'.join(l)

class TestSymbolTable(unittest.TestCase):
    def test_insertGet(self):
        tbl = SymbolTable()
        tbl.insert('a', 'f', 3)
        self.assertEqual(tbl.read('a', 'f'), 3)

        self.assertRaises(AssertionError, lambda: tbl.insert('a', 'f', 3))
        tbl.insert('a', 'g', 3)

        self.assertTrue('a' in tbl)
        self.assertFalse('b' in tbl)

class Scope:
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

    def init_instance(self, instance_uid):
        instance = Scope()
        instance.name = self.name
        instance.uid = self.uid
        instance.instance_uid = instance_uid
        assert self.instance_uid is None
        instance.symbol_tbl = self.symbol_tbl
        instance.persists = self.persists
        assert self.persists
        instance.parent = self.parent
        instance.symbol_values = {}
        instance.children = self.children
        instance.tmp_cnt = self.tmp_cnt
        return instance

    def __str__(self):
        l = []
        l.append('name: {}, uid: {}, instance_uid: {}'.format(self.name, self.uid, self.instance_uid))

        if self.persists:
            l.append('PERSISTS')

        l.append('Values:{}'.format(self.symbol_values))

        l.append('symbols: ')
        l.append(str(self.symbol_tbl))
        l.append('')
        return '\n'.join(l)

    def insert(self, sym, field, value):
        if sym not in self.symbol_tbl:
            'must init all symbols with type value first'
            assert field == TYPE

        if field == VALUE:
            #     assert self.read(sym, TYPE) == value.type
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
            self.visit(child)



class ScopeTreePrinter(ScopeTreeVisitor):
    def __init__(self):
        self.indent_cnt = 0

    def _print(self, s):
        indent_str = self.indent_cnt * 4 * ' '
        print( '\n'.join((indent_str + ln for ln in s.split('\n'))))

    def visit(self, scope):
        self._print(str(scope))
        self.indent_cnt  += 1
        self.visit_children(scope)
        self.indent_cnt  -= 1




class ScopeEntry:
    def __init__(self, ctx):
        self._ctx = ctx

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ctx._exit_scope()

class GentleScopeEntry:
    def __init__(self, ctx):
        self._ctx = ctx

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ctx._gently_exit_scope()



class Context:
    def __init__(self):
        none_scope = Scope()
        none_scope.name = 'none scope'

        self._scopes_by_uid = {None:none_scope}
        self._cur_scope = None
        self._scope_history = []
        self._root = None
        self._instance_uid_count = 0

    @property
    def cur_scope(self):
        return self._cur_scope

    def add_new_scopes(self, scope_list):
        for scope in scope_list:
            assert scope.uid not in self._scopes_by_uid
            self._scopes_by_uid[scope.uid] = scope
            if not scope.parent:
                assert self._root is None
                self._root = scope

    def init_obj(self, uid):
        self._instance_uid_count += 1
        instance_uid = ("obj", self._instance_uid_count)
        base = self._scopes_by_uid[uid]
        instance = base.init_instance(instance_uid)
        if instance.parent:
            instance.parent.children.append(instance)
        self._scopes_by_uid[instance_uid] = instance
        return instance_uid


    def enter_scope(self, uid):
        self._scope_history.append(self._cur_scope)
        self._cur_scope = self._scopes_by_uid[uid]
        return ScopeEntry(self)

    def _gently_enter_scope(self, uid):
        self._scope_history.append(self._cur_scope)
        self._cur_scope = self._scopes_by_uid[uid]
        return GentleScopeEntry(self)

    def cur_scope_uid(self): # does not include instance_uid
        return self._cur_scope.uid

    def _exit_scope(self):
        if not self._cur_scope.persists:
            self._cur_scope.symbol_values = {}
        self._cur_scope = self._scope_history.pop()


    def _gently_exit_scope(self):
        self._cur_scope = self._scope_history.pop()


    def init_symbol(self, typed_sym, typed_value, pos):
        self.declare_symbol(typed_sym, pos)
        self.assign_value(typed_sym.sym, typed_value, pos)

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


    def assign_value(self, sym, value, pos):
        for scope in self._scope_hierarchy():
            if sym in scope:
                # TODO verify this is type_checked elsewhere
                # new_value = type_sys_assign(scope.read(sym, TYPE), t_value, pos)
                scope.insert(sym, VALUE, value)
                return
        raise SymbolNotFound(sym, pos)

    def assign_value_at(self, uid, sym, value, pos):
        with self._gently_enter_scope(uid):
            for scope in self._scope_hierarchy():
                if sym in scope:
                    # TODO verify this is type_checked elsewhere
                    # new_value = type_sys_assign(scope.read(sym, TYPE), t_value, pos)
                    scope.insert(sym, VALUE, value)
                    return
            raise SymbolNotFound(sym, pos)



    def read(self, sym, field, pos):
        for scope in self._scope_hierarchy():
            if sym in scope:
                return scope.read(sym, field)
        raise SymbolNotFound(sym, pos)

    def read_from_scope(self, sym, scope_uid, field, pos):
        with self._gently_enter_scope(scope_uid):
            return self.read(sym, field, pos)


if __name__ == '__main__':
    unittest.main()
