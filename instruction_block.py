class Block(list):
    @property
    def pos(self):
        return self[0].pos

    @property
    def uid(self):
        return self.pos

