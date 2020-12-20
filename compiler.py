#! /usr/bin/python3

import subprocess
import sys
import unittest
from compile_cpp import compile_cpp
from position import Position
from exceptions import LarkErrorWithPos
from instruction_tree_compiler import InstrnTreeCompiler
from instruction_tree_runner import InstrnTreeRunner
from call_stack import CallStack
from instruction_tree_visitor import  InstrnTreePrinter
from context import Context, ScopeTreePrinter
from lark import Lark
from lark.exceptions import LarkError, UnexpectedEOF, UnexpectedInput
from virtual_machine import VirtualMachine
from instruction_generator import InstructionGenerator

from scope_maker import ScopeMaker

# TODO cmd line arg, propagate thru program..
TAB_SIZE = 4

# FIXME something is holding on to state somehow

class Compiler:
    def __init__(self):
        self._reset()
        self.parser = Lark.open('syntax.lark', propagate_positions=True)
        self.exprn_parser = Lark.open('syntax.lark', parser='lalr', propagate_positions=True, start='exprn')
        self.instruction_generator = InstructionGenerator()
        self.scope_maker = ScopeMaker()



    def _reset(self):
        self.context = Context()
        self.call_stack = CallStack()
        self.virtual_machine = VirtualMachine()
        self.tree_runner = InstrnTreeRunner(self.virtual_machine, self.context, self.call_stack, self)
        self.tree_compiler = InstrnTreeCompiler(self.virtual_machine, self.context, self.call_stack, self)
        self.src_fname = None
        self.src = None

    def _set_file(self, src_fname, src=None):
        self._reset()
        self.src_fname = src_fname
        if src:
            self.src = src.expandtabs(TAB_SIZE)
            return
        with open(src_fname, 'r') as src_file:
            self.src = ''.join(src_file.readlines()).expandtabs(TAB_SIZE)

    def run_statement_code(self, src, pos):
        src = src.expandtabs(TAB_SIZE)
        try:
            ast = self.parser.parse(src)
        except LarkError as e:
            raise LarkErrorWithPos(e, pos)

        instrn_tree = self.instruction_generator.gen_instrn_tree(ast, pos.filename+'mixin')

        itp = InstrnTreePrinter()
        itp.start(instrn_tree)

        scopes = self.scope_maker.make_scopes(instrn_tree, self.context.cur_scope)
        self.context.add_new_scopes(scopes)

        scope_printer = ScopeTreePrinter()
        scope_printer.visit(self.context.cur_scope)


        self.tree_runner.run(instrn_tree)
        scope_printer.visit(self.context.cur_scope)


    def run_exprn_code(self, src, pos):
        src = src.expandtabs(TAB_SIZE)
        try:
            ast = self.exprn_parser.parse(src)
        except LarkError as e:
            raise LarkErrorWithPos(e, pos)
        print(ast.pretty())
        instrn_tree = self.instruction_generator.gen_instrn_tree(ast, self.src_fname)

        itp = InstrnTreePrinter()
        itp.start(instrn_tree)

        self.tree_runner.run(instrn_tree)



    def run_exprn_tree(self, tree, pos):
        self.tree_runner.run(tree)

    def _on_error(self, error):
        print('\n#### ERROR')
        try:
            raise error
        except UnexpectedInput as e:
            print(e)
            print(e.get_context(self.src))
        except UnexpectedEOF as e:
            print(e)
        except LarkErrorWithPos as e:
            print(e.lark_error)
            print(e.pos)
        print('####')


    def _run_file(self):

        ast = self.parser.parse(self.src)


        print(ast.pretty())
        instrn_tree = self.instruction_generator.gen_instrn_tree(ast, self.src_fname)

        itp = InstrnTreePrinter()
        itp.start(instrn_tree)

        scopes = self.scope_maker.make_scopes(instrn_tree)
        self.context.add_new_scopes(scopes)

        scope_printer = ScopeTreePrinter()
        scope_printer.visit(scopes[0])

        with self.context.enter_scope(instrn_tree.uid):
            self.tree_runner.run(instrn_tree)
            scope_printer.visit(scopes[0])
            self.run_exprn_code('main()', Position('nowhere', 0,0,0,0))

    def run_file(self, fname, src=None):
        print('~'*90)
        print('Running File: ' + fname)
        self._set_file(fname, src)
        try:
            self._run_file()
        except LarkError as e:
            self._on_error(e)
        print('~'*90)

    def compile_statements(self, src,  pos):
        src = src.expandtabs(TAB_SIZE)
        try:
            ast = self.parser.parse(src)
        except LarkError as e:
            raise LarkErrorWithPos(e, pos)

        sub_tree = self.instruction_generator.gen_instrn_tree(ast, pos.filename+'mixin')

        scopes = self.scope_maker.make_scopes(sub_tree, self.context.cur_scope)
        self.context.add_new_scopes(scopes)

        return sub_tree

    def compile_exprn_code(self, src,  pos):
        src = src.expandtabs(TAB_SIZE)
        try:
            ast = self.exprn_parser.parse(src)
        except LarkError as e:
            raise LarkErrorWithPos(e, pos)

        sub_tree = self.instruction_generator.gen_instrn_tree(ast, pos.filename+'mixin')

        return sub_tree




    def _compile_file(self):
        ast = self.parser.parse(self.src)

        print(ast.pretty())
        instrn_tree = self.instruction_generator.gen_instrn_tree(ast, self.src_fname)

        itp = InstrnTreePrinter()
        itp.start(instrn_tree)

        scopes = self.scope_maker.make_scopes(instrn_tree)
        self.context.add_new_scopes(scopes)

        scope_printer = ScopeTreePrinter()
        scope_printer.visit(scopes[0])

        with self.context.enter_scope(instrn_tree.uid):
            code = self.tree_compiler.compile_tree(instrn_tree)
            print('\n'.join(code))
            compile_cpp(code)



    def compile_file(self, fname, src=None):
        # print('~'*90)
        print('Running File: ' + fname)
        self._set_file(fname, src)

        try:
            self._compile_file()
        except LarkError as e:
            self._on_error(e)
        # print('~'*90)




def main():
    compiler = Compiler()
    compiler.run_file('test_code/big.lang')
    # compiler.compile_file('test_code/operators.lang')

def grammer_test():

    parser = Lark.open('syntax.lark', parser='lalr', propagate_positions=True)


    for fname in (
                    'test_code/basic.lang',
                    'test_code/big.lang',
                    'test_code/classes.lang',
                    'test_code/func_call.lang',
                    'test_code/mixin_fail.lang',
                    'test_code/mixin.lang',
                    'test_code/operators.lang',
                    'test_code/grammer_test.lang',
                    ):
        with open(fname) as src_file:
            src = ''.join(src_file.readlines()).expandtabs(TAB_SIZE)
        print('------- ' + fname + '-------------')
        tree = parser.parse(src)
        print(tree.pretty())



if __name__ == '__main__':

    # main()
    rtncode = subprocess.run([sys.executable, '-m', 'unittest', 'discover']).returncode
    # print(rtncode)
    # if not rtncode:
        # grammer_test()
