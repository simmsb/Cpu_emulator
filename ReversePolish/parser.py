
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
        return 'MOV @stk @acc\nPOPSTK @stk\nADD @stk\nPOPSTK @stk\nPUSHSTK @acc\n'

    @operator('-')
    def sub():
        return 'MOV @stk @acc\nPOPSTK @stk\nSUB @stk\nPOPSTK @stk\nPUSHSTK @acc\n'

    @operator('*')
    def mul():
        return 'MOV @stk @acc\nPOPSTK @stk\nMUL @stk\nPOPSTK @stk\nPUSHSTK @acc\n'

    @operator('/')
    def div():
        return 'MOV @stk @acc\nPOPSTK @stk\nDIV @stk\nPOPSTK @stk\nPUSHSTK @acc\n'

class Parser(OperatorSet):
    def __init__(self, source):
        self.source = source
        super().__init__()
        self.compiled = self.compile()

    def compile(self):
        text = ''
        for i in self.source:
            if i.isdigit():
                text+='PUSHSTK {}\n'.format(i)
            elif self.ops.get(i):
                text+= self.ops.get(i)()
        text+= 'PRNTINT @stk'
        return text
