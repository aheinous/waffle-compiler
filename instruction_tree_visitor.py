# class InstrnTreeVisitor:
#     def __init__(self):
#         pass

#     def start(self, instrns):
#         self.visit_new_scope('root', instrns)

#     def visit_blk(self, instrns):
#         for instrn in instrns:
#             self.visit_instrn(instrn)


#     def visit_children(self, instrn):
#         for name, child_scope in instrn.child_scopes.items():
#             self.visit_new_scope(name, child_scope)


#     def visit_instrn(self, instrn):
#         self.visit_children(instrn)

#     def visit_new_scope(self, name, instrns):
#         self.visit_blk(instrns)


class InstrnTreeVisitor:
    def __init__(self, error=False):
        self._error = error

    def start(self, blk):
        self.visit_new_scope('root', blk)

    def visit_blk(self, blk):
        for instrn in blk:
            self.visit_instrn(instrn)

    def visit_instrn(self, instrn):
        method_name = 'visit_' + type(instrn).__name__
        try:
            # print('method_name:', method_name)
            method = getattr(self, method_name)
        except AttributeError as e:
            if self._error:
                raise e
            method = self.visit_children
        return method(instrn)


    def visit_children(self, instrn):
        for name, child_scope in instrn.child_scopes.items():
            self.visit_new_scope(name, child_scope)

    def visit_new_scope(self, name, instrn_blk):
        self.visit_blk(instrn_blk)



class InstrnTreePrinter(InstrnTreeVisitor):
    def __init__(self):
        super().__init__()
        self.indent = 0

    def visit_instrn(self, instrn):
        print('    ' * self.indent + str(instrn))
        self.visit_children(instrn)


    def visit_new_scope(self, name, instrns):
        print('    ' * self.indent + name)
        self.indent += 1
        self.visit_blk(instrns)
        self.indent -= 1




