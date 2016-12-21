import pyparsing as pp


# generates math trees, etc


class ParseException(Exception):
    pass


class languageSyntaxOBbase:

    def __init__(self):
        self.parent = None
        self.children = []

    def parent_own_children(self):
        self.parent_children(*self.children)

    def parent_children(self, *children):
        for i in children:
            if isinstance(i, languageSyntaxOBbase):
                i.set_parent(self)
            elif isinstance(i, list):
                self.parent_children(*i)

    def set_parent(self, parent):
        self.parent = parent

    def get_variable(self, VarName):
        if not self.parent:
            raise ParseException(
                "object: {} attempted to gain variable {}, but it has no parent".format(self, VarName))

        else:
            return self.parent.get_variable(VarName)

    def assemble(self, parent):
        return ["nop"]


class mathOP(languageSyntaxOBbase):

    def __init__(self, *blocks):  # , op, b):
        super().__init__()
        self.blocks = blocks

    """parse infix expression to postfix, sub in vars"""


class assignOP(languageSyntaxOBbase):

    def __init__(self, setter, val):
        super().__init__()
        self.setter = setter
        self.val = val


class variableOB(languageSyntaxOBbase):

    def __init__(self, name, initial_val):
        super().__init__()
        self.name = name
        self.initial = initial_val


class variableList(languageSyntaxOBbase):

    def __init__(self, *variables):
        super().__init__()
        self.vars = variables


class programList(languageSyntaxOBbase):

    def __init__(self, *blocks):
        super().__init__()
        self.blocks = blocks


class languageSyntaxOB(languageSyntaxOBbase):

    def __init__(self, mytype, *blocks):
        super().__init__()
        self.blocks = blocks
        self.mytype = mytype


class functionCallOB(languageSyntaxOBbase):

    def __init__(self, *blocks):
        super().__init__()
        self.blocks = blocks


class functionDefineOB(languageSyntaxOBbase):

    def __init__(self, *blocks):
        super().__init__()
        self.blocks = blocks


class comparisonOB(languageSyntaxOBbase):

    def __init__(self, *blocks):
        super().__init__()
        self.blocks = blocks


class funcBase(languageSyntaxOBbase):

    def __init__(self, name, params, *blocks):
        super().__init__()
        self.blocks = blocks
        self.name = name
        self.params = params
        self.vars = []

    def get_variable(self, VarName):
        if not self.parent:
            raise ParseException(
                "object: {} attempted to gain variable {}, but it has no parent".format(self, VarName))

        else:
            '''
            func wew(a,b,c){
                vars{
                    d:=0;
                    e:=4;
                }
                program{
                    return a
                }
            }


            stack; |var| position relative to @lstk, position in var/ param list:

            |a|  + 3, 0
            |b|  + 2, 1
            |c|  + 1, 2
            |old stack pointer| +- 0
            |d|  - 1, 0
            |e|  - 2, 1

            '''
            if VarName in self.params:
                return "[@lstk+{}]".format(self.params[::-1].index(VarName) + 1)
            elif VarName in self.vars:
                return "[@lstk-{}]".format(self.vars.index(VarName) + 1)
            else:
                raise ParseException(
                    "Attempt to access variable not in scope. Current function: {}, variable: {}".format(self.name, VarName))


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
        arg = pp.Group(self.funcStructure) | self.operand
        args = arg + pp.ZeroOrMore(self.comma + arg)

        self.funcStructure << self.variable + \
            pp.Group(self.lparen + pp.Optional(args) + self.rparen)
        self.funcStructure.setParseAction(lambda s, l, t: functionCallOB(*t))

        self.FuncCall = self.funcStructure + self.semicol

    def parse(self, string):
        return self.funcStructure.parseString(string).asList()

    @property
    def in_op(self):
        """something := func()
        func(func2());"""
        return self.FuncCall

    @property
    def inline(self):
        """func();"""
        return self.funcStructure


class AssignmentSolver(FuncCallSolver):

    def __init__(self):
        super().__init__()
        operator = self.funcStructure | self.operand

        addsub = pp.oneOf("+ -")
        muldiv = pp.oneOf("* /")

        oplist = [
            (muldiv, 2, pp.opAssoc.RIGHT),
            (addsub, 2, pp.opAssoc.RIGHT)
        ]

        expr = pp.operatorPrecedence(operator, oplist).setParseAction(
            lambda s, l, t: mathOP(t.asList()))

        assign = self.variable + self.equals + expr
        self.assignment_call = assign + self.semicol
        self.assignment_call.setParseAction(lambda s, l, t: assignOP(*t))

    def parse(self, string):
        return self.assignment_call.parseString(string).asList()

    @property
    def parseObject(self):
        return self.assignment_call


class SyntaxBlockParser(SolverBase):

    def __init__(self):
        super().__init__()
        program = AssignmentSolver().parseObject | FuncCallSolver().inline
        self.languageSyntaxOBject = pp.Forward()

        Syntaxblk = pp.OneOrMore(pp.Group(self.languageSyntaxOBject) | program)

        condition = self.lparen + self.operand + \
            self.comparison + self.operand + self.rparen
        condition.setParseAction(lambda s, l, t: comparisonOB(*t))

        syntaxBlocks = pp.oneOf("while if")

        self.languageSyntaxOBject << syntaxBlocks + condition + \
            self.opening_curly_bracket + Syntaxblk + self.closing_curly_bracket
        self.languageSyntaxOBject.setParseAction(
            lambda s, l, t: languageSyntaxOB(*t))

    def parse(self, string):
        return self.languageSyntaxOBject.parseString(string).asList()

    @property
    def parseObject(self):
        return self.languageSyntaxOBject


class OperationsObjects(SolverBase):

    def __init__(self):
        super().__init__()
        SyntaxBlocks = SyntaxBlockParser().parseObject
        assignBlocks = AssignmentSolver().parseObject
        functionCallBlocks = FuncCallSolver().inline

        self.operation = SyntaxBlocks | assignBlocks | functionCallBlocks

    def parse(self, string):
        return self.operation.parseString(string).asList()

    @property
    def parseObject(self):
        return self.operation


class ProgramObjects(OperationsObjects):

    def __init__(self):
        super().__init__()

        self.program = pp.Word("program").suppress(
        ) + self.opening_curly_bracket + pp.OneOrMore(self.operation) + self.closing_curly_bracket
        self.program.setParseAction(lambda s, l, t: programList(*t))

    def parse(self, string):
        return self.program.parseString(string).asList()

    @property
    def parseObject(self):
        return self.program


class FunctionDefineParser(SolverBase):

    def __init__(self):
        super().__init__()
        program = ProgramObjects().parseObject

        varline = self.variable + self.equals + self.integer + self.semicol
        varline.setParseAction(lambda s, l, t: variableOB(*t))
        varsblock = pp.Word("vars").suppress(
        ) + self.opening_curly_bracket + pp.OneOrMore(varline) + self.closing_curly_bracket
        varsblock.setParseAction(lambda s, l, t: variableList(*t))

        args = self.operand + pp.ZeroOrMore(self.comma + self.operand)

        argblock = self.lparen + pp.Optional(args) + self.rparen

        startblock = pp.Word("func ").suppress(
        ) + self.variable + argblock + self.opening_curly_bracket
        startblock.setParseAction(lambda s, l, t: funcBase(*t))

        self.function = startblock + \
            pp.Optional(varsblock) + program + self.closing_curly_bracket
        self.function.setParseAction(lambda s, l, t: functionDefineOB(*t))

    def parse(self, string):
        return self.function.parseString(string).asList()

    @property
    def parseObject(self):
        return self.function


class ProgramSolver:

    def __init__(self):
        self.functions = FunctionDefineParser().function


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
