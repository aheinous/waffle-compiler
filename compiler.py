#! /usr/bin/python3

from lark import Lark

from virtual_machine import VirtualMachine, VMRuntimeException
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
    gen = InstructionGenerator(vm)

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
    print(exprn)


    print('---------------------------------------------------------------------')


if __name__ == '__main__':
    with  open('syntax.lark', 'r') as synfile:
        syntax = ''.join(synfile.readlines())

    parser = Lark(syntax)


    # run('''
    # func f(var y, var a, var b){
    #     return 3 + a;
    # }

    # var x = 2*f(3, 10, 100);




    # ''')


    run('''
        func f(){
            return;
        }
        var x = f();

        f();

    ''')