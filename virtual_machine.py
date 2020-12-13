

from type_system import TypedStr, TypedValue


class VirtualMachine:
    def __init__(self):
        self._run_stack = []
        self._comp_stack = []



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




    def __str__(self):
        s =  'VM:\n\tRunStack' + str(self._run_stack) \
                + '\n\tCompStack' + str(self._comp_stack)
        return s

