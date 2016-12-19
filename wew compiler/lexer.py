import pyparsing as pp


# generates math trees, etc


class ParseException(Exception):
    pass


class mathtest:
    def __init__(self, op):
        print(op)


class mathOP:

    def __init__(self, op):  # , op, b):
        self.op = op


class assignOP:

    def __init__(self, setter, val):
        self.setter = setter
        self.val = val


class variableOB:

    def __init__(self, name, initial_val):
        self.name = name
        self.initial = initial_val

class variableList:
    
    def __init__(self, *variables):
        self.vars = variables


class programList:
    def __init__(self, *blocks):
        self.blocks = blocks


class syntaxOB:
    def __init__(self, mytype, *blocks):
        self.blocks = blocks
        self.mytype = mytype

class functionCallOB:
    def __init__(self, *blocks):
        self.blocks = blocks

class functionDefineOB:
    def __init__(self, *blocks):
        self.blocks = blocks


class comparisonOB:
    def __init__(self, *blocks):
        self.blocks = blocks


class funcBase:
    def __init__(self, *blocks):
        self.blocks = blocks
 


class SolverBase:

    def __init__(self):
        self.integer = pp.Word(pp.nums).setParseAction(lambda t: int(t[0]))
        self.variable = pp.Word(pp.alphas + "_", pp.alphanums + "_", exact=0)
        self.operand = self.integer | self.variable
        self.semicol = pp.Literal(";").suppress()
        self.equals = pp.Literal(":=").suppress()

        self.opening_curly_bracket = pp.Literal("{").suppress()
        self.closing_curly_bracket = pp.Literal("}").suppress()

        self.lparen = pp.Literal("(").suppress()
        self.rparen = pp.Literal(")").suppress()
        self.comma = pp.Literal(",").suppress()

        self.comparison = pp.oneOf("== != > < >= <=")


class FuncCallSolver(SolverBase):

    def __init__(self):
        super().__init__()
        self.funcStructure = pp.Forward()
        self.arg = pp.Group(self.funcStructure) | self.operand
        self.args = self.arg + pp.ZeroOrMore(self.comma + self.arg)


        self.funcStructure << self.variable + \
            pp.Group(self.lparen + pp.Optional(self.args) + self.rparen)
        self.funcStructure.setParseAction(lambda s, l, t: functionCallOB(*t))

        self.func_call = self.funcStructure + self.semicol

    def parse(self, string):
        return self.funcStructure.parseString(string).asList()


class AssignmentSolver(FuncCallSolver):

    def __init__(self):
        super().__init__()
        self.operator = self.funcStructure | self.operand

        self.addsub = pp.oneOf("+ -")
        self.muldiv = pp.oneOf("* /")

        self.oplist = [
            (self.muldiv, 2, pp.opAssoc.RIGHT),
            (self.addsub, 2, pp.opAssoc.RIGHT)
        ]

        self.expr = pp.operatorPrecedence(self.operator, self.oplist).setParseAction(
            lambda s, l, t: mathOP(t.asList()))

        self.assign = self.variable + self.equals + self.expr
        self.assignment_call = self.assign + self.semicol
        self.assignment_call.setParseAction(lambda s, l, t: assignOP(*t))

    def parse(self, string):
        return self.assignment_call.parseString(string).asList()
       



class SyntaxBlockParser(SolverBase):

    def __init__(self):
        super().__init__()
        self.program = AssignmentSolver().assignment_call | FuncCallSolver().func_call
        self.SyntaxObject = pp.Forward()
        self.Syntaxblk = pp.OneOrMore(pp.Group(self.SyntaxObject) | self.program)

        self.condition = self.lparen + self.operand + self.comparison + self.operand + self.rparen
        self.condition.setParseAction(lambda s, l, t: comparisonOB(*t))

        self.syntaxBlocks = pp.oneOf("while if")

        self.SyntaxObject << self.syntaxBlocks + self.condition + self.opening_curly_bracket + self.Syntaxblk + self.closing_curly_bracket
        self.SyntaxObject.setParseAction(lambda s,l,t: syntaxOB(*t))
    
    def parse(self, string):
        return self.SyntaxObject.parseString(string).asList()



class OperationsObjects(SolverBase):
    def __init__(self):
        super().__init__()
        self.SyntaxBlocks = SyntaxBlockParser().SyntaxObject
        self.assignBlocks = AssignmentSolver().assignment_call
        self.functionBlocks = FuncCallSolver().func_call

        # TODO: add if statement

        self.operation = self.SyntaxBlocks | self.assignBlocks | self.functionBlocks
    
    def parse(self, string):
        return self.operation.parseString(string).asList()



class ProgramObjects(OperationsObjects):
    def __init__(self):
        super().__init__()

        self.program = pp.Word("program").suppress() + self.opening_curly_bracket + pp.OneOrMore(self.operation) + self.closing_curly_bracket
        self.program.setParseAction(lambda s, l, t: programList(*t))

    def parse(self, string):
        return self.program.parseString(string).asList()


class FunctionDefineParser(SolverBase):

    def __init__(self):
        super().__init__()
        self.program = ProgramObjects()

        self.varline = self.variable + self.equals + self.integer + self.semicol
        self.varline.setParseAction(lambda s, l, t: variableOB(*t))
        self.varsblock = pp.Word("vars").suppress(
        ) + self.opening_curly_bracket + pp.OneOrMore(self.varline) + self.closing_curly_bracket
        self.varsblock.setParseAction(lambda s, l, t: variableList(*t))


        self.arg = self.operand
        self.args = self.arg + pp.ZeroOrMore(self.comma + self.arg)

        self.argblock = self.lparen + pp.Optional(self.args) + self.rparen

        self.startblock = pp.Word("func ").suppress(
        ) + self.variable + self.argblock + self.opening_curly_bracket
        self.startblock.setParseAction(lambda s,l,t: funcBase(*t))

        self.function = self.startblock + pp.Optional(self.varsblock) + self.program.program + self.closing_curly_bracket
        self.function.setParseAction(lambda s,l,t: functionDefineOB(*t))

    def parse(self, string):
        return self.function.parseString(string).asList()


if __name__ == "__main__":
    a = OperationsObjects()


    print(a.parse("wew();"))
    print(a.parse("wew(lad, ayy, lmao);"))
    print(a.parse("wew(lad);"))
    print(a.parse("wew(lad(ayy), ayy);"))
    print(a.parse("wew(lad(ayy(lmao(test))));"))
    print(a.parse("wew(lad(ayy()));"))

    print(a.parse("A := A + B - C;"))
    print(a.parse("A := func() + c * 5;"))

    print(a.parse("while(a>b){wew();lad(wew());if(a<b){dothis();}}}"))

    b = FunctionDefineParser()
    print(b.parse("func wew(a,b,c){vars{a:=2;b:=4;}program{call();}}"))
