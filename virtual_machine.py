from instructions import Func
from type_system import *
from copy import deepcopy



class VirtualMachine:
    def __init__(self, start_ctx):
        self._run_stack = []
        self._comp_stack = []


        self.run_ctx = start_ctx
        self.comp_ctx = start_ctx
        # self.run_ctx = start_ctx

        # self._comp_tmpcnt = 0
        # self._comp_call_stack = []
        # self.comp_ctx = deepcopy(start_ctx)


    def comp_push(self, typed_str):
        assert isinstance(typed_str, TypedStr)
        self._comp_stack.append(typed_str)

    def comp_pop(self):
        return self._comp_stack.pop()



    def run_push(self, data):
        assert isinstance(data, TypedValue)
        self._run_stack.append(data)

    def run_pop(self):
        return self._run_stack.pop()

    def run_peek(self):
        return self._run_stack[-1]



    def call(self, sym, pos):
        func = self.run_ctx.read_symbol(sym, pos).value
        func.run(self)



    def __str__(self):
        s =  'VM:\n\tRunStack' + str(self._run_stack) \
                + '\n\tCompStack' + str(self._comp_stack)
        for sym, value in self.run_ctx.global_symbols.items():
                s += '\n\t{}: {}'.format(sym, value)
        return s


    def run(self, instrns=None):
        if instrns is None:
            instrns = self.run_ctx.instrns
        for instrn in instrns:
            instrn.run(self)

    def compile(self, instrs=None):
        wholeProgram = False
        if instrs is None:
            wholeProgram = True
            instrs = self.comp_ctx.instrns

        code = []
        for instr in instrs:
            instrCode = instr.compile(self)
            if isinstance(instrCode, str):
                code.append(instrCode)
            else:
                assert isinstance(instrCode, list)
                code += instrCode

        funcCode = []

        if wholeProgram:
            for func in self.comp_ctx.global_symbols.values():
                func = func.value
                if not isinstance(func, Func):
                    continue

                funcCode += func.compile(self)
                funcCode += ['']


        return funcCode + code
