#! /usr/bin/python3

from lark import Lark
from lark.exceptions import UnexpectedInput

from virtual_machine import VirtualMachine, VMRuntimeException
from instruction_generator import InstructionGenerator, Position


def run(code, fname='<no-file>'):

    print('---------------------------------------------------------------------')
    print(code)
    try:
        tree = parser.parse(code)
    except UnexpectedInput as e:
        print(e)
        print('Occurred at {}:{}:{}'.format(fname, e.line, e.column))
        print(e.get_context(code))
        return
    print('### tree')
    print(tree)
    print(tree.pretty())


    print("### Tree interpreter")
    vm = VirtualMachine()
    gen = InstructionGenerator(vm, fname)

    gen.visit(tree)
    print(vm)

    print('### Run')
    try:
        vm.run()
    except VMRuntimeException as rte:
        print('ERROR: ' + str(rte))

    print(vm)


    print('### compile')
    code = '\n'.join(vm.compile())
    print(code)

    print(vm)

    print('###')
    print(code)


    print('---------------------------------------------------------------------')


if __name__ == '__main__':
    with  open('syntax.lark', 'r') as synfile:
        syntax = ''.join(synfile.readlines())

    parser = Lark(syntax, parser='lalr', propagate_positions=True)


    run('''
    y = 30;



    ''')

    # UnexpectedInput

    # run('''
    # var x = 2 + 3;

    # ''')

    # def add_src_orgin_arg(func):
    #     def wrapper(self, tree):
    #         src_origin = SrcOrigin(self.fname, tree.line, tree.column)
    #         func(self, tree, src_origin)
    #     return wrapper

