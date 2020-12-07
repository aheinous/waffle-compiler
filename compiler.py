#! /usr/bin/python3

from lark import Lark

from virtual_machine import VirtualMachine, VMRuntimeError
from instruction_generator import InstructionGenerator


def run(exprn):

    print('---------------------------------------------------------------------')
    print(exprn)
    tree = parser.parse(exprn)
    print('### tree')
    print(tree)
    print(tree.pretty())


    print("### Tree interpreter")
    vm = VirtualMachine()
    ti = InstructionGenerator(vm)

    ti.visit(tree)
    print(vm)

    print('### Run')
    try:
        vm.run()
    except VMRuntimeError as rte:
        print('ERROR: ' + str(rte))

    print(vm)


    print('### compile')
    code = '\n'.join(vm.compile())
    print(code)

    print(exprn)


    print('---------------------------------------------------------------------')


if __name__ == '__main__':
    with  open('syntax.lark', 'r') as synfile:
        syntax = ''.join(synfile.readlines())

    parser = Lark(syntax)


    run('''
        var z = 0;
        func foo(var x, var m){
            z = 2*x;
            z = z * m;
        }

        var p = 10;
        foo(2, p*10);



    ''')
