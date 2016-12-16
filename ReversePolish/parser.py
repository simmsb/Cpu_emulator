
ops = {}

def operator(op):
    def deco(func):
        ops[op] = func
        return func
    return deco

class OperatorSet:
    def __init__(self):
        self.ops = ops.copy()

    @operator('+')
    def add():
        return ['POPSTK @eax','POPSTK @acc','ADD @eax','PUSHSTK @acc']

    @operator('-')
    def sub():
        return ['POPSTK @eax','POPSTK @acc','SUB @eax','PUSHSTK @acc']

    @operator('*')
    def mul():
        return ['POPSTK @eax','POPSTK @acc','MUL @eax','PUSHSTK @acc']

    @operator('/')
    def div():
        return ['POPSTK @eax','POPSTK @acc','DIV @eax','PUSHSTK @acc']

class Parser(OperatorSet):
    def __init__(self, source):
        self.source = source
        super().__init__()
        self.compiled = self.compile()

    def compile(self):
        text = []
        for i in self.source:
            if i.isdigit():
                text.append('PUSHSTK #{}'.format(i))
            elif self.ops.get(i):
                text += self.ops.get(i)()
        text += ['PRNTINT [@stk+0]', 'PRNTNL', 'HALT']
        return text
