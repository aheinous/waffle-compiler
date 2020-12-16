class Block(list):
    def __init__(self, *vargs, **kwargs):
        super().__init__(*vargs, **kwargs)
        self.persistent_scope = False

    @property
    def pos(self):
        if not self:
            return None
        return self[0].pos

    @property
    def uid(self):
        return self.pos

