from exceptions import RtnException
from type_system import TypedValue, Void, check_assign_okay, op_res
from context import VALUE
from instruction_tree_visitor import InstrnTreeVisitor


class InstrnTreeRunner(InstrnTreeVisitor):
    def __init__(self, vm, ctx, call_stack, compiler):
        super().__init__()
        self.vm = vm
        self.ctx = ctx
        self.call_stack = call_stack
        self.compiler = compiler


    def run(self, instrn_blk):
        self.visit_blk(instrn_blk)


    def visit_Assign(self, assign):
        typed_value = self.vm.run_pop()
        self.ctx.assign_symbol(assign.sym, typed_value, assign.pos)

    def visit_Decl(self, decl):
        self.ctx.declare_symbol(decl.typed_sym, decl.pos)

    def visit_Push(self, push):
        self.vm.run_push(self.ctx.read(push.sym, VALUE, push.pos))

    def visit_Pushi(self, push):
        self.vm.run_push(push.value)

    def visit_Pop(self, pop):
        self.vm.run_pop()

    def visit_BinOp(self, binop):
        right = self.vm.run_pop()
        left = self.vm.run_pop()
        self.vm.run_push(op_res(binop.op, left, right, binop.pos))


    def visit_UnaryOp(self, unaryop):
        operand = self.vm.run_pop()
        self.vm.run_push(op_res(unaryop.op, operand, unaryop.pos))


    def visit_IfElse(self, ifelse):
        self.run(ifelse.condBlk)
        cond = self.vm.run_pop().value
        if cond:
            with self.ctx.enter_scope(ifelse.ifBlk.uid):
                self.run(ifelse.ifBlk)
        else:
            with self.ctx.enter_scope(ifelse.elseBlk.uid):
                self.run(ifelse.elseBlk)


    def visit_WhileLoop(self, while_loop):
        while True:
            self.run(while_loop.condBlk)
            cond = self.vm.run_pop()
            if not cond.value:
                break
            with self.ctx.enter_scope(while_loop.loop.uid):
                self.run(while_loop.loop)


    def visit_InitFunc(self, init_func):
        self.ctx.init_symbol(init_func.typed_sym, init_func.typed_func, init_func.pos)

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


    def visit_Mixin(self, mixin):
        self.run(mixin.exprn)
        s = self.vm.run_pop()
        self.compiler.run_exprn_code(s.value, mixin.pos)

    def visit_MixinStatements(self, mixin):
        self.run(mixin.statements)
        s = self.vm.run_pop()
        self.compiler.run_statement_code(s.value, mixin.pos)
