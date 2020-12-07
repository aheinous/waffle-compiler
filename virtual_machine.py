from instructions import Func

class RAIIInstrDest:
    def __init__(self, vm, instrs):
        self._vm = vm
        self._instrs = instrs

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._vm._popInstrDest()

    def getInstrs(self):
        return self._instrs


class VMRuntimeError(Exception):
    def __init__(self, desc):
        super().__init__(desc)


class ScopeMgr:
    def __init__(self):
        self._scopeStack = [{}]

    def __str__(self):
        s = "ScopeMgr:"
        for scope in self._scopeStack:
            s += '\n\t' + str(scope)
        return s

    @property
    def local_scope(self):
        return self._scopeStack[-1]

    @property
    def globalScope(self):
        return self._scopeStack[0]

    def __contains__(self, sym):
        for scope in reversed(self._scopeStack):
            if sym in scope:
                return True
        return False

    def putGlobalScope(self, sym, value):
        if sym in self._scopeStack[0]:
            raise VMRuntimeError('Global symbol reassignment: ' + sym)
        self._scopeStack[0][sym] = value

    def __getitem__(self, sym):
        for scope in reversed(self._scopeStack):
            if sym in scope:
                return scope[sym]
        # assert False
        raise VMRuntimeError('Symbol not found: ' + str(sym))

    def inLocalScope(self, sym):
        return sym in self.local_scope

    def decl(self, sym, value):
        if self.inLocalScope(sym):
            raise VMRuntimeError('Symbol reassignment: ' + sym)
        self.local_scope[sym] = value

    def assign(self, sym, value):
        for scope in reversed(self._scopeStack):
            if sym in scope:
                scope[sym] = value
                return
        raise VMRuntimeError('Assignment to non-declared symbol: ' + sym)


    def push(self):
        self._scopeStack.append({})

    def pop(self):
        self._scopeStack.pop()




class VirtualMachine:
    def __init__(self):
        self._instrsDestStack = [[]]
        self._run_dataStack = []
        self.run_ctx = ScopeMgr()

        self.comp_varStack = []
        self.comp_varCnt = 0

    def comp_push(self, val):
        name = 'tmp_{}'.format(self.comp_varCnt)
        self.comp_varStack.append(name)
        code = 'int {} = {};'.format(name, val)
        self.comp_varCnt += 1
        return code

    def comp_pushi(self, val):
        self.comp_varStack.append(str(val))
        return []

    # def comp_pushSym(self, val):
    #     self.comp_varStack.append(str(val))
    #     return []



    def comp_pop(self):
        return self.comp_varStack.pop()


    def run_push(self, data):
        self._run_dataStack.append(data)

    def run_pop(self):
        return self._run_dataStack.pop()

    def addInstr(self, instr):
        self._instrs().append(instr)

    def addFunc(self, sym, func):
        self.run_ctx.putGlobalScope(sym, func)

    def call(self, sym):
        func = self.run_ctx[sym]
        func.run(self)

    def _instrs(self):
        return self._instrsDestStack[-1]

    def newInstrDest(self):
        self._instrsDestStack.append([])
        return RAIIInstrDest(self, self._instrsDestStack[-1])

    def _popInstrDest(self):
        self._instrsDestStack.pop()


    def __str__(self):
        return 'VM:\n\t' + str(self._instrs()) + '\n\t' + str(self._run_dataStack) \
                + '\n\t' + str(self.run_ctx)


    def run(self, instrs=None):
        if instrs is None:
            instrs = self._instrs()
        for instr in instrs:
            instr.run(self)

    def compile(self, instrs=None):
        wholeProgram = False
        if instrs is None:
            wholeProgram = True
            instrs = self._instrs()

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
            for sym, func in self.run_ctx.globalScope.items():
                if not isinstance(func, Func):
                    continue

                funcCode += func.compile(self)
                funcCode += ['']


        return funcCode + code
