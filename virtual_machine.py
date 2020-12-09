from typing import TypeVar
from instructions import Func
from exceptions import VMRuntimeException, TypeMismatchException
from type_checking import *
from copy import copy as shallow_copy, deepcopy



class VirtualMachine:
    def __init__(self, start_ctx):
        # self._instrsDestStack = [[]]
        self._run_stack = []
        self.run_ctx = start_ctx
        # self._run_call_stack = []

        self._comp_stack = []
        self._comp_tmpcnt = 0
        self.comp_ctx = deepcopy(start_ctx) # TODO enter/exit scopes
        self._comp_call_stack = []

    def comp_push(self, val):
        assert isinstance(val, TypedValue)
        name = 'tmp_{}'.format(self._comp_tmpcnt)
        self._comp_stack.append(TypedValue(name, val.type))
        code = '{} {} = {};'.format(val.type, name, val.value)
        self._comp_tmpcnt += 1
        return code

    def comp_pushi(self, val):
        assert isinstance(val, TypedValue)
        self._comp_stack.append(val)
        return []

    def comp_push_sym(self, sym, who):
        assert isinstance(sym, str)
        typed_value = self.comp_ctx.read_symbol(sym, who)
        typed_sym = TypedSym(sym, typed_value.type)
        self._comp_stack.append(typed_sym)
        return []


    def comp_push_fragment(self, sym, fragment, who):
        assert isinstance(sym, str)
        val = self.comp_ctx.read_symbol(sym, who)
        val = TypedValue(fragment, val.type)
        self._comp_stack.append(val)
        return []



    def comp_pop(self):
        return self._comp_stack.pop()



    def run_push(self, data):
        assert isinstance(data, TypedValue)
        self._run_stack.append(data)

    def run_pop(self):
        return self._run_stack.pop()

    def run_peek(self):
        return self._run_stack[-1]




    def call(self, sym, who):
        func = self.run_ctx.read_symbol(sym, who).value
        # self._run_call_stack.append(func)
        func.run(self)



    def __str__(self):
        return 'VM:\n\tRunStack' + str(self._run_stack) \
                + '\n\tCompStack' + str(self._comp_stack) \
                + '\n\t' + str(self.run_ctx.global_symbols)


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
