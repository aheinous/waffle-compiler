from collections import namedtuple


_Position = namedtuple('Position', ['filename', 'ln', 'col'])

class Position(_Position):
    def __str__(self):
        return '{}:{}:{}'.format(self.filename, self.ln, self.col)

    def __repr__(self):
        return self.__str__()

class _NoOne:
    def __init__(self):
        self.pos = _Position('no where', 0, 0)

NoOne = _NoOne()
