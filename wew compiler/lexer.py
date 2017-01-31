import copy
from formatter import format_string

import pyparsing as pp

# generates math trees, etc

# this

JID = 0  # label counter


class no_depth_list(list):
    """Class that does not allow any nested lists to be appended, any iterables appended will be unpacked first """

    def __lshift__(self, other):
        try:
            for i in other:
                self << i
        except:  # not iterable, so just append other
            self.append(other)


class ParseException(Exception):
    pass


class languageSyntaxOBbase:
    """Base class for language objects"""

    def __init__(self, children):
        self.parent = None
        self.children = children

    def parent_own_children(self):
        """Initiates filling of child parents (for codegen callbacks)"""
        # print("{0} parenting children: {0.children}".format(self))
        self.parent_children(self.children)

    def parent_children(self, *children):
        for i in children:
            if isinstance(i, languageSyntaxOBbase):
                i.set_parent(self)
                i.parent_own_children()
            elif isinstance(i, (list, tuple, pp.ParseResults)):
                self.parent_children(*i)

    def set_parent(self, parent):
        self.parent = parent

    def get_variable(self, VarName):
        """Finds stack position of a variable, bubbles up to the parent function"""
        if not self.parent:
            raise ParseException(
                "object: {} attempted to gain variable {}, but it has no parent".
                format(self, VarName))

        else:
            # this should bubble up to the parent function
            return self.parent.get_variable(VarName)

    def assemble(self):
        return no_depth_list(["nop"])

    @property
    def num_params(self):
        return self.parent.num_params

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <children: {1}>>".format(
            self, ", ".join("{}".format(str(i)) for i in self.children))


class mathOP(languageSyntaxOBbase):

    def __init__(self, *children):  # , op, b):
        super().__init__(children)

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <children: {1}>>".format(
            self, ", ".join("{}".format(str(i)) for i in self.children))

    def assemble(self):
        """
        Use stack, infix -> postfix ->the stack machine -> return variable in @RET
        """
        ...   # TODO: This pls


class assignOP(languageSyntaxOBbase):

    def __init__(self, setter, val):
        self.setter = setter
        self.val = val

        super().__init__(val)

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <setter: {0.setter}> <val: {0.val}>>".format(
            self)

    def assemble(self):
        variable = self.get_variable(self.setter)
        left_side = self.val.assemble()
        # output of left_side always ends in @ACC

        out = no_depth_list()
        for i in left_side:
            out << left_side
        out << f"MOV @ACC {variable}"
        return out


class variableOB(languageSyntaxOBbase):

    def __init__(self, name, initial_val):
        super().__init__()
        self.name = name
        self.initial = initial_val

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <name: {0.name}> <initial: {0.initial}>>".format(
            self)

    def __eq__(self, other):
        return self.name == other


class programList(languageSyntaxOBbase):

    def __init__(self, *children):
        super().__init__()
        self.children = children

    def assemble(self):
        out = no_depth_list()
        for i in self.children:
            out << i.assemble()

        return out


class comparisonOB(languageSyntaxOBbase):

    replaceMap = {  # inversed, skips
        "<": "meje",
        ">": "leje",
        "==": "nqje",
        "!=": "eqje",
        ">=": "lje",
        "<=": "mje"
    }

    def __init__(self, left, comp, right):
        super().__init__()
        self.comp = self.replaceMap[comp]
        self.left = left
        self.right = right

    def __str__(self):
        return "<{0.__class__.__name__}:{0.comp} <parent: {0.parent.__class__.__name__}> <lhs: {0.left}> <rhs: {0.right}>>".format(
            self)


class whileTypeOB(languageSyntaxOBbase):

    def __init__(self, comp, *codeblock):
        super().__init__()
        self.comp = comp
        self.codeblock = codeblock
        self.children = [self.codeblock, self.comp]

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <comparison: {0.comp}> <codeblock: {1}>>".format(
            self, ", ".join("{}".format(str(i)) for i in self.codeblock))

    def assemble(self):
        out = no_depth_list()
        out << f"_jump_start_{JID} CMP {self.get_variable(self.comp.left)} {self.get_variable(self.comp.right)}"
        out << f"{self.comp.comp} jump_end_{JID}"
        for i in self.codeblock:
            out << i.assemble()
        out << f"JMP jump_start_{JID}"
        out << f"_jump_end_{JID} NOP"

        JID += 1

        return out


class ifTypeOB(languageSyntaxOBbase):

    def __init__(self, comp, *codeblock):
        super().__init__()
        self.comp = comp
        self.codeblock = codeblock
        self.children = [self.codeblock, self.comp]

    def assemble(self):
        out = no_depth_list()
        out << f"CMP {self.get_variable(self.comp.left)} {self.get_variable(self.comp.right)}"
        out << f"{self.comp.comp} jump_end_{JID}"
        for i in self.codeblock:
            out << i.assemble()
        out << f"_jump_end_{JID} NOP"

        JID += 1

        return out

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <comparison: {0.comp}> <codeblock: {1}>>".format(
            self, ", ".join("{}".format(str(i)) for i in self.codeblock))


def languageSyntaxOB(type_, *children):
    types = {  # TODO: correct parser to do any form of "word (stuff) {code}"
        "while": whileTypeOB,
        "if": ifTypeOB
    }

    return types[type_](*children)


class functionCallOB(languageSyntaxOBbase):

    def __init__(self, functionName, children):
        super().__init__()
        self.functionName = functionName
        self.children = children

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <name: {0.functionName}> <args: {1}>>".format(
            self, ", ".join("{}".format(str(i)) for i in self.children))


class varList(languageSyntaxOBbase):

    def __init__(self, *children):
        super().__init__()
        self.children = children


class functionDefineOB(languageSyntaxOBbase):

    def __init__(self, name, params, vars_, children):
        super().__init__()
        self.name = name
        self.params = params
        self.vars_ = vars_
        self.children = children

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <name: {0.name}> <params: {0.params}> <vars: {0.vars_}> <children: {0.children}>>".format(
            self)

    def get_variable(self, VarName):
        if not self.parent:
            raise ParseException(
                "object: {} attempted to gain variable {}, but it has no parent".
                format(self, VarName))

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
            |old local stack pointer| +- 0
            |d|  - 1, 0
            |e|  - 2, 1

            '''
            if VarName in self.params:
                return "[@lstk+{}]".format(self.params.vars_[::-1].index(
                    VarName) + 1)
            elif VarName in self.vars:
                return "[@lstk-{}]".format(self.vars_.vars_index(VarName) + 1)
            else:
                raise ParseException(
                    "Attempt to access variable not in scope. Current function: {}, variable: {}".
                    format(self.name, VarName))

        @property
        def num_params(self):
            return len(self.params)


class returnStmtOB(languageSyntaxOBbase):

    def assemble(self):
        out = no_depth_list()
        """
        how to return:
            move returned variable to @RET
            move @LSTK to @STK (reset stack pointer)
            move [@LSTK] to @STK (return old pointer)
            add <number of vars> to @STK (push stack above pointer)
            call RET
        """
        out << f"MOV {} @RET"
        out << "MOV @LSTK @STK"
        out << "MOV [@STK+0] @LSTK"
        out << "MOV @STK @ACC"
        out << f"ADD {self.num_params}"
        out << "MOV @ACC @STK"
        out << "RET"


class atoms:
    integer = pp.Word(pp.nums).setParseAction(lambda t: int(t[0]))
    variable = pp.Word(pp.alphas + "_", pp.alphanums + "_", exact=0)
    operand = integer | variable
    semicol = pp.Literal(";").suppress()
    equals = pp.Literal(":=").suppress()

    opening_curly_bracket = pp.Literal("{").suppress()
    closing_curly_bracket = pp.Literal("}").suppress()

    lparen = pp.Literal("(").suppress()
    rparen = pp.Literal(")").suppress()
    comma = pp.Literal(",").suppress()

    comparison = pp.oneOf("== != > < >= <=")


class FuncCallSolver:
    functionCall = pp.Forward()
    arg = functionCall | atoms.operand
    args = arg + pp.ZeroOrMore(atoms.comma + arg)
    args.setParseAction(lambda t: varList(*t))

    functionCall << atoms.variable + \
        pp.Group(atoms.lparen + pp.Optional(args) + atoms.rparen)
    functionCall.setParseAction(lambda s, l, t: functionCallOB(*t))

    functionCallInline = functionCall + atoms.semicol


class AssignmentSolver:
    operator = FuncCallSolver.functionCall | atoms.operand

    addsub = pp.oneOf("+ -")
    muldiv = pp.oneOf("* /")

    oplist = [(muldiv, 2, pp.opAssoc.RIGHT), (addsub, 2, pp.opAssoc.RIGHT)]

    expr = pp.operatorPrecedence(
        operator,
        oplist).setParseAction(lambda s, l, t: mathOP(t.asList()))

    assign = atoms.variable + atoms.equals + expr
    assignmentCall = assign + atoms.semicol
    assignmentCall.setParseAction(lambda s, l, t: assignOP(*t))


class SyntaxBlockParser:

    program = AssignmentSolver.assignmentCall | FuncCallSolver.functionCallInline
    languageSyntaxObject = pp.Forward()

    Syntaxblk = pp.OneOrMore(pp.Group(languageSyntaxObject) | program)

    condition = atoms.lparen + atoms.operand + \
        atoms.comparison + atoms.operand + atoms.rparen
    condition.setParseAction(lambda s, l, t: comparisonOB(*t))

    syntaxBlocks = pp.oneOf("while if")

    syntaxBlock << syntaxBlocks + condition + \
        atoms.opening_curly_bracket + Syntaxblk + atoms.closing_curly_bracket
    syntaxBlock.setParseAction(
        lambda s, l, t: languageSyntaxOB(*t))


class returnStatement:

    statements = (pp.Word("return").suppress() +
                  atoms.variable).setParseAction(lambda t: returnStmtOB(*t))


class OperationsObjects:

    SyntaxBlocks = SyntaxBlockParser.syntaxBlock
    assignBlocks = AssignmentSolver.assignmentCall
    functionCallBlocks = FuncCallSolver.inline
    statements = returnStatement.return_  # consistency TODO: refactor

    operation = SyntaxBlocks | assignBlocks | functionCallBlocks | statements


class ProgramObjects(OperationsObjects):

    program = pp.Word("program").suppress() + atoms.opening_curly_bracket + pp.OneOrMore(
        operation) + atoms.closing_curly_bracket
    self.program.setParseAction(lambda s, l, t: programList(*t))


class FunctionDefineParser(SolverBase):

    def __init__(self):
        super().__init__()
        program = ProgramObjects().parseObject

        var_assign_line = atoms.variable + atoms.equals + atoms + atoms.semicol
        var_assign_line.setParseAction(lambda s, l, t: variableOB(*t))
        var_noassign_line = atoms.variable + atoms.semicol
        var_noassign_line.setParseAction(
            lambda s, l, t: variableOB(*t, 0))  # init with 0
        varline = var_assign_line | var_noassign_line
        varsblock = pp.Word("vars").suppress(
        ) + atoms.opening_curly_bracket + pp.OneOrMore(
            varline) + atoms.closing_curly_bracket
        varsblock.setParseAction(lambda s, l, t: varList(*t))

        arg = copy.copy(atoms.variable)
        arg.setParseAction(lambda s, l, t: variableOB(*t, 0))

        args = atoms.variable + pp.ZeroOrMore(atoms.comma + atoms.variable)

        argblock = atoms.lparen + pp.Optional(args) + atoms.rparen
        argblock.setParseAction(lambda s, l, t: varList(*t))

        func_name = copy.copy(atoms.variable)
        func_name.setParseAction()

        startblock = pp.Word("func ").suppress(
        ) + atoms.variable + argblock + atoms.opening_curly_bracket

        self.function = startblock + \
            pp.Optional(varsblock, default=None) + \
            program + atoms.closing_curly_bracket
        self.function.setParseAction(lambda s, l, t: functionDefineOB(*t))


class ProgramSolver:

    def __init__(self):
        self.functions = pp.OneOrMore(FunctionDefineParser().function)

    def parse(self, string):
        return self.functions.parseString(string).asList()


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

    c = ProgramSolver()
    parsed = c.parse(
        "func main(wew, lad){vars{wew;}program{while(1<2){callthis();}wew:=3;}}"
    )[0]  # Type: functionDefineOB
    parsed.parent_own_children()
    print(format_string(str(parsed)))

    second = c.parse(
        "func main(a){program{if(this==that){a:=4;call(a);}while(1<3){print(this, more, that());}}} func call(a,b,c){vars{d;e:=333;f:=3;}program{d:=a*b*c;}}")
    for i in second:
        i.parent_own_children()
        print(format_string(str(i)))
