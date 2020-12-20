from exceptions import MixinException
import unittest
import io
import sys
from compiler import Compiler

class Tester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # cls.compiler = Compiler()
        pass

    def setUp(self):
        self.compiler = Compiler()


    def runCode_getLocals(self,fname, src):
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        try:
            self.compiler.run_file(fname, src)
        finally:
            sys.stdout = sys.__stdout__
        return self.extractLocals( capturedOutput.getvalue())

    def compileCode_getLocals(self,fname, src):
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput
        try:
            self.compiler.compile_file(fname, src)
        finally:
            sys.stdout = sys.__stdout__
        return self.extractLocals( capturedOutput.getvalue())


    def preprocessLocals(self, locals):
        for sym, val, type_ in locals:
            if type_ == 'float':
                val = float(val)
            yield (sym, val, type_)

    def extractLocals(self, output):
        start_delim = 'vvvvv PLocal vvvvv'
        end_delim = '^^^^^ PLocal ^^^^^'

        starti = output.rfind(start_delim) + len(start_delim)
        endi = output.rfind(end_delim)
        # print(output)
        if starti == -1 or endi == -1:
            print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            print(output)
            print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            assert False
        output = output[starti : endi]

        try:
            locals = set()
            for ln in output.split('\n'):
                if ';' in ln:
                    sym, val, type_ = (s.strip() for s in ln.split(';'))
                    locals.add((sym,val, type_))
            return locals
        except Exception as e:
            print(output)
            raise e

    def run_tests(self, fname, locals):
        with open('test_code/'+fname) as srcfile:
            src = ''.join(srcfile.readlines())

        locals = self.preprocessLocals(locals)
        runLocals = self.preprocessLocals(self.runCode_getLocals(fname, src))
        compileLocals = self.preprocessLocals(self.compileCode_getLocals(fname, src))
        locals = set(locals)
        runLocals = set(runLocals)
        compileLocals = set(compileLocals)

        self.assertEqual(runLocals , locals)
        self.assertEqual(compileLocals, locals)

    def runFile(self, fname):
        with open('test_code/'+fname) as srcfile:
            src = ''.join(srcfile.readlines())
        self.compiler.run_file(fname, src)

    def compileFile(self, fname):
        with open('test_code/'+fname) as srcfile:
            src = ''.join(srcfile.readlines())
        self.compiler.compile_file(fname, src)




    def test_basic(self):
        self.run_tests('basic.lang', {
            ('x', '100', 'int')
        })

    def test_operators(self):
        self.run_tests('operators.lang', {
            ('x', '1529', 'int'),
            ('a', '-5', 'int'),
            ('b', '5', 'int'),
            ('d', '20', 'int'),
            ('e', '0', 'int'),
            ('f', '1', 'int'),
            ('g', '0', 'int'),
            ('h', '1', 'int'),
            ('i', '0', 'int'),
            ('j', '0', 'int'),
            ('k', '1', 'int'),
        })


    def test_funcCall(self):
        self.run_tests('func_call.lang', {
            ('x', '58', 'int')
        })



    def test_big(self):
        self.run_tests('big.lang', {
            ('a', '-5', 'int'),
            ('b', '5', 'int'),
            ('c', '11', 'int'),
            ('d', '20', 'int'),
            ('e', '220', 'int'),
            ('f', '7.1', 'float'),
            ('h', '2', 'float'),
            ('i', '120', 'int'),
        })

    def test_mixin(self):
        self.run_tests('mixin.lang', {
            ('a', '10', 'int'),
            ('b', '57', 'int'),
            ('c', '15', 'int'),
            ('d', '500', 'int'),
            ('e', '10', 'int'),
            ('f', '17', 'int'),
        })

    def test_mixinErrors(self):
        with self.assertRaises(MixinException):
            self.compileFile('mixin_fail.lang')