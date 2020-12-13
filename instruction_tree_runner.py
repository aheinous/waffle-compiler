from exceptions import RtnException
from type_system import TypedValue, Void, check_assign_okay, op_res
from context import VALUE
from instruction_tree_visitor import InstrnTreeVisitor


class InstrnTreeRunner(InstrnTreeVisitor):
    def __init__(self, vm, ctx, call_stack):
        super().__init__()
        self.vm = vm
        self.ctx = ctx
        self.call_stack = call_stack


    def run(self, instrn_blk):
        self.visit_blk(instrn_blk)


    def visit_Assign(self, instrn):
        typed_value = self.vm.run_pop()
        self.ctx.assign_symbol(instrn.sym, typed_value, instrn.pos)

    def visit_Decl(self, decl):
        self.ctx.declare_symbol(decl.typed_sym, decl.pos)

    def visit_Push(self, instrn):
        self.vm.run_push(self.ctx.read(instrn.sym, VALUE, instrn.pos))

    def visit_Pushi(self, instrn):
        self.vm.run_push(instrn._value)

    def visit_Pop(self, instrn):
        self.vm.run_pop()

    def visit_BinOp(self, instrn):
        right = self.vm.run_pop()
        left = self.vm.run_pop()
        self.vm.run_push(op_res(instrn.op, left, right, instrn.pos))


    def visit_UnaryOp(self, instrn):
        operand = self.vm.run_pop()
        self.vm.run_push(op_res(instrn.op, operand, instrn.pos))


    def visit_IfElse(self, instrn):
        # self.vm.run(self._condBlk, ctx)
        # self._condBlk.run(self.vm, self.ctx)
        self.run(instrn._condBlk)
        cond = self.vm.run_pop().value
        # with self.ctx.raii_push_scope():
        if cond:
            with self.ctx.enter_scope(instrn._ifBlk.uid):
                # self.vm.run(instrn._ifBlk, self.ctx)
                self.run(instrn._ifBlk)
        else:
            with self.ctx.enter_scope(instrn._elseBlk.uid):
                # self.vm.run(instrn._elseBlk, self.ctx)
                self.run(instrn._elseBlk)


    def visit_WhileLoop(self, instrn):
        while True:
            # self.vm.run(self._condBlk, self.ctx)
            # self._condBlk.run(self.vm, self.ctx)
            self.run(instrn._condBlk)
            cond = self.vm.run_pop()
            if not cond.value:
                break
            with self.ctx.enter_scope(instrn.loop.uid):
                # self.vm.run(self._loop, self.ctx)
                # self._loop.run(self.vm, self.ctx)
                self.run(instrn.loop)


    def visit_InitFunc(self, instrn):
        self.ctx.init_symbol(instrn._typed_sym, instrn._typed_func, instrn.pos)

    def visit_Call(self, call):
        # Call
        for instrns in call.arg_exprns:
            self.run(instrns)
        t_func = self.ctx.read(call.func_sym, VALUE, call.pos)
        func = t_func.value

        # Func
        with self.call_stack.push(func), self.ctx.enter_scope(func.instrns.uid):
            for arg in reversed(func.args):
                self.ctx.init_symbol(arg, self.vm.run_pop(), func.pos)
            try:
                # self.instrns.run( self.vm, self.ctx)
                self.run(func.instrns)
            except RtnException as e:
                pass




    def visit_Rtn(self, rtn):
        if rtn.exprn:
            self.run(rtn.exprn)
        else:
            self.vm.run_push(TypedValue(None, Void()))
        check_assign_okay(self.call_stack.peek().rtn_type, self.vm.run_peek().type, rtn.pos)
        raise RtnException()


