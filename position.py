from collections import namedtuple


_Position = namedtuple('Position', ['filename', 'ln', 'col', 'end_ln', 'end_col'])

class Position(_Position):


    def __str__(self):
        return '{}:{}:{} -> {}:{}'.format(   self.filename,
                                            self.ln,
                                            self.col,
                                            self.end_ln,
                                            self.end_col
                                            )

    def __repr__(self):
        return self.__str__()

