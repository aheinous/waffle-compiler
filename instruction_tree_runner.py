from instructions import ClassDecl
from type_system import Void
from exceptions import RtnException
from typed_data import LValue, RValue
from context import TYPE, VALUE
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
        r_value = self.vm.run_pop()
        l_value = self.vm.run_pop()
        l_value.assign(r_value, self.ctx, assign.pos)

    def visit_Decl(self, decl):
        self.ctx.declare_symbol(decl.typed_sym, decl.pos)

    def visit_Push(self, push):
        l_value = LValue(
            push.sym,
            self.ctx.read(push.sym, TYPE, push.pos),
            self.ctx.cur_scope_uid()

        )
        self.vm.run_push(l_value)

    def visit_Pushi(self, push):
        self.vm.run_push(push.value)

    def visit_Pop(self, pop):
        self.vm.run_pop()

    def visit_BinOp(self, binop):
        right = self.vm.run_pop()
        left = self.vm.run_pop()
        self.vm.run_push(left.binOpRes(binop.op, right, self.ctx, binop.pos))


    def visit_UnaryOp(self, unaryop):
        operand = self.vm.run_pop()
        self.vm.run_push(operand.unaryOpRes(unaryop.op, self.ctx, unaryop.pos))

    def visit_IfElse(self, ifelse):
        self.run(ifelse.condBlk)
        cond = self.vm.run_pop().value(self.ctx, ifelse.pos)
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
            if not cond.value(self.ctx, while_loop.pos):
                break
            with self.ctx.enter_scope(while_loop.loop.uid):
                self.run(while_loop.loop)


    def visit_InitFunc(self, init_func):
        self.ctx.init_symbol(init_func.typed_sym, init_func.typed_func, init_func.pos)

    def visit_Call(self, call):
        # Call
        for instrns in call.arg_exprns:
            self.run(instrns)

        t_callable = self.ctx.read(call.func_sym, VALUE, call.pos)
        callable = t_callable.value(self.ctx, call.pos)


        if isinstance(callable, ClassDecl):
            self.initObject(callable)
        else:

            func = callable
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
            self.vm.run_push(RValue(None, Void()))
        rtnVal = self.vm.run_pop()
        self.call_stack.checkRtnTypeOkay(rtnVal, rtn.pos)
        self.vm.run_push(rtnVal.rvalue(self.ctx, rtn.pos))
        raise RtnException()


    def visit_Mixin(self, mixin):
        self.run(mixin.exprn)
        s = self.vm.run_pop()
        self.compiler.run_exprn_code(s.value(self.ctx, mixin.pos), mixin.pos)

    def visit_MixinStatements(self, mixin):
        self.run(mixin.statements)
        s = self.vm.run_pop()
        # code = s.value(self.ctx, mixin.pos) + ';'

        self.compiler.run_statement_code(s.value(self.ctx, mixin.pos)+';', mixin.pos)

    def visit_ClassDecl(self, class_decl):
        # with self.ctx.enter_scope(class_decl.contents.uid):
        #     self.visit_blk(class_decl.contents)

        self.ctx.init_symbol(       class_decl.t_sym,
                                    RValue(class_decl, class_decl.t_sym.type),
                                    class_decl.pos)


    def initObject(self, classDecl):
        instance_id = self.ctx.init_obj(classDecl.uid)
        self.vm.run_push(RValue(instance_id, classDecl.type))

        with self.ctx.enter_scope(instance_id):
            self.run(classDecl.contents)







    # def visit_ObjectInit(self, obj_init):
    #     instance_id = self.ctx.init_obj(obj_init.type.uid)
    #     self.vm.run_push(RValue(instance_id, obj_init.type))

    def visit_PLocal(self, plocal):
        localvar = self.ctx.cur_scope.symbol_values
        localvar = sorted(localvar.items())
        print('vvvvv PLocal vvvvv')
        for sym, val in localvar:
            print('{} ; {} ; {}'.format(sym, val.value(), val.type_repr))
        print('^^^^^ PLocal ^^^^^')
