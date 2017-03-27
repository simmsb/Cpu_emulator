import pyparsing as pp


class Register:

    def __init__(self, name):
        self.name = name

    def find(self, cpu):
        return cpu.registers[self.name.lower()]

    def __str__(self):
        return f"<reg {self.name}>"


class Immediate:

    def __init__(self, imm):
        self.imm = imm

    def find(self, cpu):
        return int(self.imm)

    def __str__(self):
        return f"<imm of {self.imm}>"


class Dereference:

    def __init__(self, location):
        self.location = location

    def find(self, cpu):
        return cpu.memory[self.location.find(cpu)]

    def __str__(self):
        return f"<deref of {self.location}>"


class Math:

    def __init__(self, *operation):
        self.operation = operation

    def find(self, cpu):

        class binaryop:

            def __init__(self, left, op, right):
                self.left = left
                self.op = op
                self.right = right

            def find(self, cpu):
                if self.op == "+":
                    return self.left.find(cpu) + self.right.find(cpu)
                elif self.op == "-":
                    return self.left.find(cpu) - self.right.find(cpu)

        def consume(left, op, right, *rest):
            if not rest:
                return binaryop(left, op, right)
            return consume(binaryop(left, op, right), *rest)
        if len(self.operation) == 1:
            return self.operation[0].find(cpu)
        return consume(*self.operation).find(cpu)

    def __str__(self):
        return f"<math: ops = {[str(i) for i in self.operation]}>"


class LocationParse:

    lsqrbrk = pp.Literal("[").suppress()
    rsqrbrk = pp.Literal("]").suppress()

    integer = pp.Word(pp.nums).setParseAction(lambda t: int(t[0]))

    register = (pp.Literal("@").suppress() + pp.Word(pp.srange("[a-zA-Z]"))
                ).setParseAction(lambda t: Register(*t))
    immediate = integer.copy().setParseAction(lambda t: Immediate(*t))

    dereference = pp.Forward()

    combination = immediate ^ register ^ dereference

    addsub = pp.oneOf("+ -")
    mathop = combination + pp.ZeroOrMore(addsub + combination)
    mathop.setParseAction(lambda t: Math(*t))

    dereference << lsqrbrk + (mathop ^ combination) + rsqrbrk
    dereference.setParseAction(lambda t: Dereference(*t))

    parsed = combination ^ mathop ^ dereference


def parseLocation(locstring, cpu):
    """
    Parse a location, returning it's result.
    [xxx] := value stored at memory location xxx
    a + b := value of a + value of b
    [a+1] := value contained at memory location (a + 1)
    """
    data = LocationParse.parsed.parseString(locstring).asList()
    result = data[0].find(cpu)
    return result
