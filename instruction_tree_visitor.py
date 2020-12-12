class InstrnTreeVisitor:
    def __init__(self):
        pass

    def start(self, instrns):
        self.on_visit_new_scope('root', instrns)

    def visit(self, instrns):
        for instrn in instrns:
            self.on_visit_instrn(instrn)


    def visit_children(self, instrn):
        for name, child_scope in instrn.child_scopes.items():
            self.on_visit_new_scope(name, child_scope)


    def on_visit_instrn(self, instrn):
        self.visit_children(instrn)

    def on_visit_new_scope(self, name, instrns):
        self.visit(instrns)


class InstrnTreePrinter(InstrnTreeVisitor):
    def __init__(self):
        self.indent = 0

    def on_visit_instrn(self, instrn):
        print('    ' * self.indent + str(instrn))
        self.visit_children(instrn)


    def on_visit_new_scope(self, name, instrns):
        print('    ' * self.indent + name)
        self.indent += 1
        self.visit(instrns)
        self.indent -= 1
