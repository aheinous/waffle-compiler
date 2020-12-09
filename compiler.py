#! /usr/bin/python3

# from instructions import TypedValue
from lark import Lark
from lark.exceptions import UnexpectedInput

from virtual_machine import VirtualMachine, VMRuntimeException
from instruction_generator import InstructionGenerator, Position
from type_checking import *

def compile(src_fname):
    parser = Lark.open('syntax.lark', parser='lalr', propagate_positions=True)
    # src_fname = 'complete.lang'
    src = ''
    with open(src_fname, 'r') as src_file:
        src = ''.join(src_file.readlines())
    tree = parser.parse(src)
    print(tree)
    print(tree.pretty())

    print("### Instruction Generator")
    gen = InstructionGenerator(src_fname)
    gen.visit(tree)

    # print(gen.results.instrns)
    for instrn in gen.results.instrns:
        print(instrn)
    vm = VirtualMachine(gen.results)

    print(vm)

    print('### Run')
    try:
        vm.run()
    except VMRuntimeException as rte:
        print('ERROR: ' + str(rte))

    print(vm)


    print('### compile')
    try:
        code = '\n'.join(vm.compile())
        print(code)
    except VMRuntimeException as rte:
        print('ERROR: ' + str(rte))

    print(vm)


def main():
    compile('complete.lang')
    compile('test.lang')

if __name__ == '__main__':
    main()