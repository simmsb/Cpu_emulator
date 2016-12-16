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


class variableOB:

    def __init__(self, name, initial_val):
        self.name = name
        self.initial = initial_val

class variableList:
    
    def __init__(self, variables):
        self.vars = variables


class programList:
    def __init__(self, blocks):
        self.blocks = blocks

 


class SolverBase:

    def __init__(self):
        self.integer = pp.Word(pp.nums).setParseAction(lambda t: int(t[0]))
        self.variable = pp.Word(pp.alphas + "_", pp.alphanums + "_", exact=0)
        self.operand = self.integer | self.variable
        self.semicol = pp.Literal(";").suppress()
        self.equals = pp.Literal(":=").suppress()

        self.opening_curly_bracket = self.opening_curly_bracket
        self.closing_curly_bracket = pp.literal("}").suppress()


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

        self.func_call = self.funcStructure + self.semicol

    def parse_line(self, line, lineno=0):
        try:
            return self.funcStructure.parseString(line).asList()
        except Exception as e:
            raise ParseException(
                "Failed parsing function call line: {}".format(lineno), e)


class AssignmentSolver(FuncSolver):

    def __init__(self):
        super().__init__()
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
        self.assignment_call = self.assign + self.semicol
        self.assignment_call.setParseAction(lambda s, l, t: assignOP(*t))

    def parse_line(self, line, lineno=0):
        try:
            return self.assignment_call.parseString(line).asList()
        except Exception as e:
            raise ParseException(
                "Failed parsing math line: {}".format(lineno), e)


class ProgramObjects(SolverBase):
    def __init__(self):
        super().__init__()
        self.assignment = AssignmentSolver()
        self.function = FuncSolver()

        self.operation = self.function.func_call | self.assignment.assignment_call

        self.program = pp.word("program").suppress() + self.opening_curly_bracket + pp.OneOrMore(self.operation) + self.closing_curly_bracket
        self.program.setParseAction(lambda s, l, t: programList(*t))


class FunctionParser(SolverBase):

    def __init__(self, code):
        super().__init__()
        self.program = ProgramObjects()
        self.code = code

        self.varline = self.variable + self.equals + self.integer + self.semicol
        self.varline.setParseAction(lambda s, l, t: variableOB(*t))
        self.varsblock = pp.word("vars").suppress(
        ) + self.opening_curly_bracket + pp.OneOrMore(self.varline) + self.closing_curly_bracket
        self.varsblock.setParseAction(lambda s, l, t: variableList(*t))

        self.startblock = pp.word("func").suppress(
        ) + self.variable + self.opening_curly_bracket

        self.endblock = self.closing_curly_bracket

        self.function = self.startblock + pp.Optional(self.varsblock) + self.program.program


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
