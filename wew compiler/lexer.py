import copy
import traceback
from formatter import format_string

import pyparsing as pp


class no_depth_list(list):
    """Class that does not allow any nested lists to be appended, any iterables appended will be unpacked first """

    def __lshift__(self, other):
        self.append(other)


class ParseException(Exception):
    pass


class languageSyntaxOBbase:
    """Base class for language objects"""

    def __init__(self, *children):
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

    @classmethod
    def assemble_list(cls, cmds):
        if isinstance(cmds, (list, tuple)):
            for i in cmds:
                yield from cls.assemble_list(i)
        elif isinstance(cmds, languageSyntaxOBbase):
            yield from cmds.assemble()

    def assemble(self):
        out = no_depth_list()
        for i in self.assemble_list(self.children):
            out << i

        return out

    @property
    def num_params(self):
        return self.parent.num_params

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <children: {1}>>".format(
            self, ", ".join("{}".format(str(i)) for i in self.children))


class mathOP(languageSyntaxOBbase):

    def __init__(self, children):  # , op, b):
        super().__init__(children)

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <children: {1}>>".format(
            self, ", ".join("{}".format(str(i)) for i in self.children))

    def assemble(self):
        """
        Use stack, infix -> postfix -> the stack machine -> return variable in @RET
        """

        asm_map = {
            "+": "ADD",
            "-": "SUB",
            "*": "MUL",
            "/": "DIV"
        }

        def parse(expr):
            resolved = []

            if isinstance(expr, (int, str)):
                return expr

            while expr:
                i = expr.pop()
                if isinstance(i, list):
                    for i in parse(i):
                        resolved.append(i)
                elif isinstance(i, mathop):
                    for i in parse(i.children):
                        resolved.append(i)
                elif i in ["+", "-", "*", "/"]:
                    next_ = parse(expr.pop())
                    prev = resolved.pop()
                    resolved += next_
                    resolved.append(prev)
                    resolved.append(i)
                else:  # string or int
                    resolved.append(i)
            return resolved

        out = no_depth_list()
        for i in parse(self.children):
            if isinstance(i, int):
                out << f"PUSHSTK #{i}"
            elif i in ["+", "-", "*", "/"]:
                out << "POPSTK @ACC"
                out << "POPSTK @EAX"
                out << f"{asm_map[i]} @EAX"
                out << "PUSHSTK @ACC"
            elif isinstance(i, str):
                out << f"PUSHSTK {self.get_variable(i)}"
            elif isinstance(i, functionCallOB):
                for i in i.assemble():
                    out << i
                out << "PUSHSTK @RET"
        out << "POPSTK @ACC"
        return out


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
        right_side = self.val.assemble()
        # output of right_side always ends in @ACC

        out = no_depth_list()
        for i in self.assemble_list(right_side):
            out << i
        out << f"MOV @ACC {variable}"

        return out


class variableOB(languageSyntaxOBbase):

    def __init__(self, name, initial_val):
        super().__init__()
        self.type = NotImplemented  # TODO: Implement types
        self.name = name
        self.initial = initial_val

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <name: {0.name}> <initial: {0.initial}>>".format(
            self)

    def __eq__(self, other):
        return self.name == other


class programList(languageSyntaxOBbase):

    def __init__(self, *children):
        super().__init__(*children)

    def assemble(self):
        out = no_depth_list()
        for i in self.assemble_list(self.children):
            out << i

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
        global JID

        out = no_depth_list()
        out << f"_jump_start_{JID} CMP {self.get_variable(self.comp.left)} {self.get_variable(self.comp.right)}"
        out << f"{self.comp.comp} jump_end_{JID}"
        for i in self.assemble_list(self.codeblock):
            out << i
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
        global JID

        out = no_depth_list()
        out << f"CMP {self.get_variable(self.comp.left)} {self.get_variable(self.comp.right)}"
        out << f"{self.comp.comp} jump_end_{JID}"
        for i in self.assemble_list(self.codeblock):
            out << i
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

    def assemble(self):
        vars_ = no_depth_list()
        stack_pos = 0
        out = no_depth_list()
        for i in self.children:
            if isinstance(i, int):
                vars_ << f"#{i}"
            elif isinstance(i, str):
                vars_ << self.get_variable(i)
            elif isinstance(i, mathOP):
                for k in i.assemble():
                    out << k
                vars_ << {"stackPosition": stack_pos}
                stack_pos += 1  # TODO:
                #
                #
                #    Turn list of vars_ into: `CALL arg1 [arg2 [...]]
                #
                #


def varList(*vars):

    return vars


class functionDefineOB(languageSyntaxOBbase):

    def __init__(self, name, params, vars_, program):
        super().__init__(program)
        self.name = name
        self.params = params
        self.vars_ = vars_

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <name: {0.name}> <params: {0.params}> <vars: {0.vars_}> <children: {1}>>".format(
            self, [str(i) for i in self.children])

    def get_variable(self, VarName):
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
        print(f"getting variable {VarName}, t: {type(VarName)}")
        ret = None
        if self.params:
            if VarName in self.params:
                return "[@lstk+{}]".format(self.params[::-1].index(VarName) + 1)
        elif self.vars_:
            if VarName in self.vars_:
                return "[@lstk-{}]".format(
                    self.vars_.index(VarName) + 1)
        else:
            raise ParseException(
                "Attempt to access variable not in scope. Current function: {}, variable: {}".
                format(self.name, VarName))

    @property
    def num_params(self):
        return len(self.params)

    def assemble(self):
        out = no_depth_list()
        out << f"_{self.name} NOP"
        out << "PUSHSTK @lstk"  # save previous stack pointer
        out << "MOV [@stk+0] @lstk"  # copy current stack pointer to @lstk
        for i in self.vars_:  # insert our function local vars
            out << f"PUSHSTK #{i.initial}"
        for i in self.assemble_list(self.children):
            out << i  # insert function code
        out << "MOV #0 @RET"  # setup fall through return function
        out << "MOV @LSTK @STK"
        out << "MOV [@STK+0] @LSTK"
        out << "MOV @STK @ACC"
        out << f"ADD #{self.num_params}"
        out << "MOV @ACC @STK"
        out << "RET"

        return out


class returnStmtOB(languageSyntaxOBbase):

    def __init__(self, returnVar):
        super().__init__()
        self.returnVar = returnVar

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
        out << f"MOV {self.get_variable(self.returnVar)} @RET"
        out << "MOV @LSTK @STK"
        out << "MOV [@STK+0] @LSTK"
        out << "MOV @STK @ACC"
        out << f"ADD #{self.num_params}"
        out << "MOV @ACC @STK"
        out << "RET"

        return out


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

    oplist = [(muldiv, 2, pp.opAssoc.LEFT), (addsub, 2, pp.opAssoc.LEFT)]

    expr = pp.infixNotation(
        operator, oplist).setParseAction(lambda s, l, t: mathOP(t.asList()))

    assign = atoms.variable + atoms.equals + expr
    assignmentCall = assign + atoms.semicol
    assignmentCall.setParseAction(lambda s, l, t: assignOP(*t))


class returnStatement:

    returnStmnt = (pp.Word("return").suppress() +
                   atoms.variable + atoms.semicol).setParseAction(lambda t: returnStmtOB(*t))


class SyntaxBlockParser:

    program = AssignmentSolver.assignmentCall | FuncCallSolver.functionCallInline | returnStatement.returnStmnt
    syntaxBlock = pp.Forward()

    Syntaxblk = pp.OneOrMore(pp.Group(syntaxBlock) | program)

    condition = atoms.lparen + atoms.operand + \
        atoms.comparison + atoms.operand + atoms.rparen
    condition.setParseAction(lambda s, l, t: comparisonOB(*t))

    blockTypes = pp.oneOf("while if")

    syntaxBlock << blockTypes + condition + \
        atoms.opening_curly_bracket + Syntaxblk + atoms.closing_curly_bracket
    syntaxBlock.setParseAction(
        lambda s, l, t: languageSyntaxOB(*t))


class OperationsObjects:

    SyntaxBlocks = SyntaxBlockParser.syntaxBlock
    assignBlocks = AssignmentSolver.assignmentCall
    functionCallBlocks = FuncCallSolver.functionCallInline
    statements = returnStatement.returnStmnt

    operation = SyntaxBlocks | assignBlocks | functionCallBlocks | statements

    @classmethod
    def parse(cls, string):
        return cls.operation.parseString(string).asList()


class ProgramObjects:

    program = pp.Word("program").suppress() + atoms.opening_curly_bracket + \
        pp.OneOrMore(OperationsObjects.operation) + atoms.closing_curly_bracket
    program.setParseAction(lambda s, l, t: programList(*t))


class FunctionDefineParser:

    var_assign_line = atoms.variable + atoms.equals + atoms.integer + atoms.semicol
    var_assign_line.setParseAction(lambda s, l, t: variableOB(*t))

    var_noassign_line = atoms.variable + atoms.semicol
    var_noassign_line.setParseAction(lambda s, l, t: variableOB(*t, 0))
    # init params that start with nothing to 0 with 0
    varline = var_assign_line | var_noassign_line
    varsblock = pp.Word("vars").suppress() + atoms.opening_curly_bracket + \
        pp.OneOrMore(varline) + atoms.closing_curly_bracket
    varsblock.setParseAction(lambda s, l, t: varList(*t))

    arg = copy.copy(atoms.variable)
    arg.setParseAction(lambda s, l, t: variableOB(*t, 0))

    args = atoms.variable + pp.ZeroOrMore(atoms.comma + atoms.variable)

    argblock = atoms.lparen + pp.Optional(args) + atoms.rparen
    argblock.setParseAction(lambda s, l, t: varList(*t))

    startblock = pp.Word("func").suppress() + atoms.variable + \
        argblock + atoms.opening_curly_bracket

    function = startblock + \
        pp.Optional(varsblock, default=None) + \
        ProgramObjects.program + atoms.closing_curly_bracket
    function.setParseAction(lambda s, l, t: functionDefineOB(*t))

    @classmethod
    def parse(cls, string):
        return cls.function.parseString(string).asList()


class ProgramSolver:

    functions = pp.OneOrMore(FunctionDefineParser().function)

    def parse(self, string):
        return self.functions.parseString(string).asList()


if __name__ == "__main__":
    JID = 0  # label counter
    a = OperationsObjects()

    print(a.parse("wew();"))
    print(a.parse("wew(lad, ayy, lmao);"))
    print(a.parse("wew(lad);"))
    print(a.parse("wew(lad(ayy), ayy);"))
    print(a.parse("wew(lad(ayy(lmao(test))));"))
    print(a.parse("wew(lad(ayy()));"))

    print(a.parse("A := A + B - C;"))
    print(a.parse("A := func() + c * 5;"))

    print(
        a.parse("while(a>b){wew();lad(wew());if(a<b){dothis();}}}"))

    b = FunctionDefineParser()
    c = ProgramSolver()
    print(format_string(
        str(c.parse("""func wew(a,b,c){
                            vars {
                                a := 2;
                                b := 4;
                            }
                            program {
                                if(this<that){
                                call();
                                }
                            }
                        }""")[0])))

    program1 = """
    func comparenums(this, that){
        vars {
            a := 2;
        }
        program {
            if (this<that) {
                return that;
            }
            return this;
        }
    }
    """
    # TODO: allow no vars, fix num_params in return statement
    min_ = program1.strip("\n")
    print(min_)

    parsed = c.parse(min_)[0]
    parsed.parent_own_children()

    print(format_string(str(parsed)))
    print("\n".join(parsed.assemble()))
