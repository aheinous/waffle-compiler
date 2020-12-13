#! /usr/bin/python3
# from instructions import InstrnTreePrinter, InstrnTreeVisitor
from instruction_tree_visitor import InstrnTreePrinter
from context import Context, ScopeTreePrinter
# from scope_mgr import ScopeMgr
from lark import Lark
from lark.exceptions import LarkError, UnexpectedInput

from virtual_machine import VirtualMachine
from instruction_generator import InstructionGenerator

from context import ScopeMaker

def compile(src_fname):
    parser = Lark.open('syntax.lark', parser='lalr', propagate_positions=True)
    src = ''
    with open(src_fname, 'r') as src_file:
        src = ''.join(src_file.readlines())
    try:
        tree = parser.parse(src)
    except LarkError as e:
        print(e)
        return
    print(tree)
    print(tree.pretty())

    print("### Instruction Generator")
    gen = InstructionGenerator(src_fname)
    gen.visit(tree)
    instructions = gen.instructions

    print()
    itp = InstrnTreePrinter()
    itp.visit(instructions)


    print('### scope maker')

    scopeMaker = ScopeMaker()
    scopeMaker.start(instructions)


    print()
    scopePrinter = ScopeTreePrinter()
    scopePrinter.visit('root', scopeMaker.scopes[0])
    print()

    print('### ctx maker')

    ctx = Context()
    ctx.add_new_scopes(scopeMaker.scopes)

    print('##### run')

    vm = VirtualMachine()
    # with ctx.enter_scope(instructions.uid):
    #     instructions.run(vm, ctx)
    #     print()
    #     scopePrinter = ScopeTreePrinter()
    #     scopePrinter.visit('root', scopeMaker.scopes[0])
    #     print()


    print('#### compile')
    with ctx.enter_scope(instructions.uid):
        # code = vm.compile(instructions)
        code = instructions.compile(vm, ctx)
        print('\n'.join(code))

    print('==============================================================')
    # sm = ScopeMgr()

    # sm.cur_scope.instrns = instructions
    # for typed_name, typed_func in gen.functions:
    #     sm.init_symbol(typed_name, typed_func, typed_func.value.pos)

    # # print(gen.results.instrns)
    # # for instrn in gen.results.instrns:
    # #     print(instrn)
    # vm = VirtualMachine(sm)

    # print(vm)

    # print('### Run')
    # vm.run()
    # # try:
    # #     vm.run()
    # # except VMRuntimeException as rte:
    # #     print('ERROR: ' + str(rte))

    # print(vm)


    # print('### compile')
    # code = '\n'.join(vm.compile())
    # print(code)
    # # try:
    # #     code = '\n'.join(vm.compile())
    # #     print(code)
    # # except VMRuntimeException as rte:
    # #     print('ERROR: ' + str(rte))

    # print(vm)


def main():
    compile('complete.lang')
    #compile('test.lang')

if __name__ == '__main__':
    main()