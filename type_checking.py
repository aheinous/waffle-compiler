from collections import namedtuple

class VoidType:
    def __eq__(self, o: object) -> bool:
        return isinstance(o, VoidType)

    def __str__(self):
        return "Void"


Void = VoidType()
_TypedValue = namedtuple('TypedValue', ['value', 'type'])


class TypedValue(_TypedValue):
	pass
