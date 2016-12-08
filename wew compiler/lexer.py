import pyparsing as pp

# generates math trees, etc

class ParseException(Exception):
    pass


class SolverBase:
    def __init__(self):
        self.integer = pp.Word(pp.nums).setParseAction(lambda t:int(t[0]))
        self.variable = pp.Word(pp.alphas+"_", pp.alphanums+"_", exact=0)
        self.operand = self.integer | self.variable
        self.semicol = pp.Literal(";").suppress()

class FuncSolver(SolverBase):
    def __init__(self):
        super().__init__()
        self.funcStructure = pp.Forward()
        self.arg = pp.Group(self.funcStructure) | self.operand
        self.args = self.arg + pp.ZeroOrMore("," + self.arg)  # we force arguments since functions have no side effects
        self.lparen = pp.Literal("(")
        self.rparen = pp.Literal(")")


        self.funcStructure << self.variable + pp.Group(self.lparen + self.args + self.rparen)

        def parse_line(self, line, lineno):
            try:
                return self.expr_def.parseString(line).asList()
            except Exception as e:
                raise ParseException("Failed parsing function call line: {}".format(lineno), e)

class AssignmentSolver(FuncSolver):
    def __init__(self):
        super().__init__()
        self.equals = pp.Literal(":=")
        self.operator = self.funcStructure | self.operand

        self.sign = pp.oneOf("+ -")
        self.addsub = pp.oneOf("+ -")
        self.muldiv = pp.oneOf("* /")

        self.oplist = [
        (self.sign, 1, pp.opAssoc.RIGHT),
        (self.muldiv, 2, pp.opAssoc.RIGHT),
        (self.addsub, 2, pp.opAssoc.RIGHT)
        ]

        self.expr = pp.operatorPrecedence(self.operator, self.oplist)

        self.assign = self.variable + self.equals + self.expr
        self.expr_def = self.assign + self.semicol


    def parse_line(self, line, lineno):
        try:
            return self.expr_def.parseString(line).asList()
        except Exception as e:
            raise ParseException("Failed parsing math line: {}".format(lineno), e)
