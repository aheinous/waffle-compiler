class Block(list):
    @property
    def pos(self):
        return self[0].pos

    @property
    def uid(self):
        return self.pos

    def run(self, machine, context):
        for instrn in self:
            instrn.run(machine, context)

    def compile(self, machine, context):
        code = []
        for instrn in self:
            instrn_code = instrn.compile(machine, context)
            if isinstance(instrn_code, str):
                code.append(instrn_code)
            else:
                assert isinstance(instrn_code, list)
                code += instrn_code
        return code