from instruction_block import Block
from instruction_tree_visitor import InstrnTreeVisitor
from context import Scope

class ScopeMaker(InstrnTreeVisitor):

    def __init__(self):
        super().__init__()
        self._stack = []
        self._scopes = []

    def _push(self, name, uid, persists=False):
        new_scope = Scope()
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

    def make_scopes(self, instrn_tree:Block, start_scope=None):
        if start_scope:
            self._stack.append(start_scope)
            self.visit_blk(instrn_tree)
        else:
            self.start(instrn_tree)

        scopes = self._scopes
        self._scopes = []
        return scopes

    def visit_new_scope(self, name:str, instrns:Block):
        if not instrns:
            return
        if len(self._scopes) == 0:
            assert name == 'root'
            instrns.persistent_scope = True
        self._push( name,
                    instrns.uid,
                    persists = instrns.persistent_scope )
        self.visit_blk(instrns)
        self._pop()
