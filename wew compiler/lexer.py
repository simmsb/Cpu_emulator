import pyparsing as pp


# generates math trees, etc


class ParseException(Exception):
    pass


class mathOP:

    def __init__(self, op):  # , op, b):
        self.op = op


class funcOP:

    def __init__(self, funcname, params):
        self.funcname = funcname
        self.params = params.asList()


class assignOP:

    def __init__(self, setter, val):
        self.setter = setter
        self.val = val


class SolverBase:

    def __init__(self):
        self.integer = pp.Word(pp.nums).setParseAction(lambda t: int(t[0]))
        self.variable = pp.Word(pp.alphas + "_", pp.alphanums + "_", exact=0)
        self.operand = self.integer | self.variable
        self.semicol = pp.Literal(";").suppress()


class FuncSolver(SolverBase):

    def __init__(self):
        super().__init__()
        self.funcStructure = pp.Forward()
        self.arg = pp.Group(self.funcStructure) | self.operand
        self.comma = pp.Literal(",").suppress()
        self.args = self.arg + pp.ZeroOrMore(self.comma + self.arg)
        self.lparen = pp.Literal("(").suppress()
        self.rparen = pp.Literal(")").suppress()

        self.funcStructure << self.variable + \
            pp.Group(self.lparen + pp.Optional(self.args) + self.rparen)
        self.funcStructure.setParseAction(lambda s, l, t: funcOP(*t))

    def parse_line(self, line, lineno=0):
        try:
            return self.funcStructure.parseString(line).asList()
        except Exception as e:
            raise ParseException(
                "Failed parsing function call line: {}".format(lineno), e)


class AssignmentSolver(FuncSolver):

    def __init__(self):
        super().__init__()
        self.equals = pp.Literal(":=").suppress()
        self.operator = self.funcStructure | self.operand

        self.sign = pp.oneOf("+ -")
        self.addsub = pp.oneOf("+ -")
        self.muldiv = pp.oneOf("* /")

        self.oplist = [
            (self.sign, 1, pp.opAssoc.RIGHT),
            (self.muldiv, 2, pp.opAssoc.RIGHT),
            (self.addsub, 2, pp.opAssoc.RIGHT)
        ]

        self.expr = pp.operatorPrecedence(self.operator, self.oplist).setParseAction(
            lambda s, l, t: mathOP(t.asList()))

        self.assign = self.variable + self.equals + self.expr
        self.expr_def = self.assign + self.semicol
        self.expr_def.setParseAction(lambda s, l, t: assignOP(*t))

    def parse_line(self, line, lineno=0):
        try:
            return self.expr_def.parseString(line).asList()
        except Exception as e:
            raise ParseException(
                "Failed parsing math line: {}".format(lineno), e)


if __name__ == "__main__":
    a = FuncSolver()
    b = AssignmentSolver()

    print(a.parse_line("wew()"))
    print(a.parse_line("wew(lad, ayy, lmao)"))
    print(a.parse_line("wew(lad)"))
    print(a.parse_line("wew(lad(ayy), ayy)"))
    print(a.parse_line("wew(lad(ayy(lmao(test))))"))
    print(a.parse_line("wew(lad(ayy()))"))

    print(b.parse_line("A := A + B - C;"))
    print(b.parse_line("A := func() + c * 5;"))
