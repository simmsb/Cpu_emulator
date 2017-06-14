from formatter import format_string

import pyparsing as pp

DEBUG = True


def debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


class no_depth_list(list):
    """Class that does not allow any nested lists to be appended, any iterables appended will be unpacked first """

    def __lshift__(self, other):
        self.append(other)


class ParseException(Exception):
    pass


class languageSyntaxOBbase:
    """Base class for language objects"""

    JID = 0  # label counter

    def __init__(self, *children):
        self.parent = None
        self.children = children

    def parent_own_children(self):
        """Initiates filling of child parents (for codegen callbacks)"""
        # debug("{0} parenting children: {0.children}".format(self))
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

    def get_variable(self, VarName, asref=False):
        """Finds stack position of a variable, bubbles up to the parent function"""
        if isinstance(VarName, int):
            return f"{VarName}"
        if not self.parent:
            raise ParseException(
                "object: {} attempted to gain variable {}, but it has no parent".
                format(self, VarName))

        else:
            # this should bubble up to the parent function
            return self.parent.get_variable(VarName, asref)

    @classmethod
    def assemble_list(cls, cmds):
        if isinstance(cmds, (list, tuple)):
            for i in cmds:
                yield from cls.assemble_list(i)
        elif isinstance(cmds, languageSyntaxOBbase):
            yield from cmds.assemble()

    def assemble(self):
        yield from self.assemble_list(self.children)

    @property
    def num_params(self):
        return self.parent.num_params

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <children: {1}>>".format(
            self, ", ".join("{}".format(str(i)) for i in self.children))


class mathOP(languageSyntaxOBbase):

    def __init__(self, children):  # , op, b):
        debug(f"Mathop: {children}")
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
            debug(f"parsing: {expr}")
            resolved = []

            if isinstance(expr, mathOP):
                return parse(expr.children)

            if isinstance(expr, (int, str, listIndexOB)):
                debug(f"ret str: {expr}")
                return expr

            if isinstance(expr, tuple):
                expr = list(expr)

            while expr:
                i = expr.pop()
                if isinstance(i, list):
                    for i in parse(i):
                        resolved.append(i)
                elif isinstance(i, mathOP):
                    for i in parse(i.children):
                        resolved.append(i)
                elif i in ["+", "-", "*", "/"]:
                    next_ = parse(expr.pop())
                    if isinstance(next_, (str, int)):
                        next_ = [next_]
                    prev = resolved.pop()
                    resolved += next_
                    resolved.append(prev)
                    resolved.append(i)
                else:  # string or int
                    resolved.append(i)
            return resolved

        parsed = parse(self.children)
        debug(parsed)
        for i in parsed:
            if isinstance(i, int):
                yield f"PUSH {i}"
            elif i in ["+", "-", "*", "/"]:
                yield "POP @EAX"
                yield "POP @ACC"
                yield f"{asm_map[i]} @EAX"
                yield "PUSH @ACC"
            elif isinstance(i, str):
                yield f"PUSH {self.get_variable(i)}"
            elif isinstance(i, functionCallOB):
                yield from i.assemble()
                yield "PUSH @RET"
            elif isinstance(i, listIndexOB):
                yield f"PUSH [{i.location}]"
        yield "POP @ACC"


class assignOP(languageSyntaxOBbase):

    def __init__(self, setter, val):
        self.setter = setter
        self.val = val

        super().__init__(setter, val)

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <setter: {0.setter}> <val: {0.val}>>".format(
            self)

    def assemble(self):
        if isinstance(self.setter, str):
            variable = self.get_variable(self.setter, asref=True)
        elif isinstance(self.setter, listIndexOB):
            variable = self.setter.location
        else:
            raise Exception(f"Undefined item to define to, itemtype = {type(self.setter)}")
        right_side = self.val.assemble()
        # output of right_side always ends in @ACC

        yield from right_side
        yield f"MOV @ACC {variable}"


class variableOB(languageSyntaxOBbase):

    def escape_char(self, char):
        d = {
            "n": "\n",
            "r": "\r"
        }
        return d.get(char, char)

    def escape_string(self, string):
        i = 0
        while i < len(string):
            if string[i] == "\\":
                i += 1
                yield self.escape_char(string[i])
            else:
                yield string[i]
            i += 1

    def __init__(self, type, name, part=None, listinitial=None, *rest):
        # if int: (type=type, name=name, part=initial)
        # if list: (type=type, name=name, part=length, listinitial=default)
        super().__init__()
        print(f"VARIABLE: name {name}, type {type}, part {part}, lstninit {listinitial}, rest: {rest}")
        self.type = type
        self.name = name
        if self.type == "list":
            if part is None and listinitial is not None:
                self.length = len(listinitial) + 1
                self.initial = map(ord, self.escape_string(listinitial + "\0"))
            elif listinitial is not None and part is not None:
                self.length = part
                self.initial = [listinitial] * part
            else:
                self.length = None
                self.initial = [None]
            self.isref = True
        else:
            self.isref = False
            self.initial = 0 if part is None else part
            self.length = 1

    def create(self):
        if self.type == "list":
            for i in self.initial:
                yield f"PUSH {i}"  # create stack space
        else:
            yield f"PUSH {self.initial}"

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <name: {0.name}> <initial: {0.initial}> <type: {0.type}> <len: {0.length}>>".format(
            self)

    def __eq__(self, other):
        return self.name == other


class programList(languageSyntaxOBbase):

    def __init__(self, *children):
        super().__init__(*children)

    def assemble(self):
        yield from self.assemble_list(self.children)


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


class ComparisonVar(languageSyntaxOBbase):

    def parseitem(self, item):
        if isinstance(item, str):
            return self.get_variable(item)
        elif isinstance(item, int):
            return f"{item}"
        elif isinstance(item, listIndexOB):
            return item.location
        else:
            raise Exception("Error parsing var of comparison")


class whileTypeOB(ComparisonVar):

    def __init__(self, comp, *codeblock):
        super().__init__()
        self.comp = comp
        self.codeblock = codeblock
        self.children = [self.codeblock, self.comp]

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <comparison: {0.comp}> <codeblock: {1}>>".format(
            self, ", ".join(str(i) for i in self.codeblock))

    def assemble(self):
        yield f"_jump_start_{self.JID} CMP {self.parseitem(self.comp.left)} {self.parseitem(self.comp.right)}"
        yield f"{self.comp.comp} jump_end_{self.JID}"
        yield from self.assemble_list(self.codeblock)
        yield f"JUMP jump_start_{self.JID}"
        yield f"_jump_end_{self.JID} NOP"

        languageSyntaxOBbase.JID += 1


class ifTypeOB(ComparisonVar):

    def __init__(self, comp, *codeblock):
        super().__init__()
        self.comp = comp
        self.codeblock = codeblock
        self.children = [self.codeblock, self.comp]

    def assemble(self):
        yield f"CMP {self.parseitem(self.comp.left)} {self.parseitem(self.comp.right)}"
        yield f"{self.comp.comp} jump_end_{self.JID}"
        yield from self.assemble_list(self.codeblock)
        yield f"_jump_end_{self.JID} NOP"

        languageSyntaxOBbase.JID += 1

    def __str__(self):
        print(type(self.codeblock))
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <comparison: {0.comp}> <codeblock: {1}>>".format(
            self, ", ".join(str(i) for i in self.codeblock))


def languageSyntaxOB(type_, *children):
    types = {  # TODO: correct parser to do any form of "word (stuff) {code}"
        "while": whileTypeOB,
        "if": ifTypeOB
    }

    return types[type_](*children)


class functionCallOB(languageSyntaxOBbase):

    def __init__(self, functionName, params=[]):
        super().__init__(*params)
        self.params = params
        self.functionName = functionName

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <name: {0.functionName}> <args: {1}>>".format(
            self, ", ".join("{}".format(str(i)) for i in self.params))

    def assemble(self):
        vars_ = no_depth_list()
        stack_pos = 0
        out = no_depth_list()
        debug(f"functioncallOB_vals: {self.params}")
        for i in self.params:
            debug(f"valinst: {i}")
            if isinstance(i, int):
                vars_ << ("val", f"{i}")
            elif isinstance(i, str):
                vars_ << ("var", self.get_variable(i))
            elif isinstance(i, listIndexOB):
                vars_ << ("var", "[" + i.location + "]")
            elif isinstance(i, mathOP):
                for k in i.assemble():
                    yield k
                yield "PUSH @ACC"
                vars_ << ("stpos", stack_pos)
                stack_pos += 1
            elif isinstance(i, functionCallOB):
                for k in i.assemble():
                    yield k
                yield "PUSH @RET"  # functions end up in the ret register
                vars_ << ("stpos", stack_pos)
                stack_pos += 1

        # decide on vars
        debug(f"VARS FOR FUNC CALL: {vars_}")

        assembled_vars = no_depth_list()
        for j, k in vars_:
            debug(f"varsdebug: name->{j}: val->{k}")
            if j == "stpos":
                assembled_vars << f"[@STK+{stack_pos+k}]"
            else:
                assembled_vars << k

                #
                #
                #    Turn list of vars_ into: `CALL arg1 [arg2 [...]]
                #
                #
        yield "CALL {} {}".format(self.functionName, " ".join(assembled_vars))
        yield "MOV @STK @ACC"  # we need to clean up our stack located arguments
        yield f"ADD {stack_pos}"
        yield "MOV @ACC @STK"
        debug(f"FUNCcOP: {out}")


def varList(*vars):  # idk TODO: Fuck this

    return vars


class listIndexOB(languageSyntaxOBbase):

    def __init__(self, name, index):
        super().__init__(index)
        self.name = name
        self.index = index

    @property
    def location(self):  # resolves index to the value at the index
        base = self.get_variable(self.name)
        if isinstance(self.index, int):  # static
            return f"{base}-{self.index}"
        if isinstance(self.index, str):  # vars
            return f"{base}-{self.get_variable(self.index)}"


class functionDefineOB(languageSyntaxOBbase):

    def __init__(self, name, params, vars_, program):
        super().__init__(program)
        self.name = name
        self.params = [] if params is None else params[::-1]
        self.vars_ = [] if vars_ is None else vars_

    def __str__(self):
        return "<{0.__class__.__name__} object: <parent: {0.parent.__class__.__name__}> <name: {0.name}> <params: {1}> <vars: {2}> <children: {3}>>".format(
            self, [str(i) for i in self.params], [str(i) for i in self.vars_], [str(i) for i in self.children])

    # gets the position of a local variable/ passed arg

    def get_variable(self, VarName, asref=False):
        '''
        returns a variables location in memory


        func wew(a,b,c){
            vars{
                d:=0;
                e:=4;
            }
            program{
                return a
            }
        }


        stack; |var| position relative to @LSTK, position in var/ param list:

        |return address| + 4
        |a|  + 3, 0
        |b|  + 2, 1
        |c|  + 1, 2
        |old local stack pointer| +- 0
        |d|  - 1, 0
        |e|  - 2, 1

        '''
        if VarName in self.params:
            index = sum(i.length for i in self.params[
                        :self.params.index(VarName)]) + 1
            # if var was passed to program as a reference, just return it
            if asref:
                return f"@lstk+{index}"
            return f"[@lstk+{index}]"
        elif VarName in self.vars_:
            index = sum(i.length for i in self.vars_[
                        :self.vars_.index(VarName)]) + 1
            var = self.vars_[self.vars_.index(VarName)]
            if var.isref or asref:
                # variable is located on the local stack frame, get a
                # reference to it
                return f"@lstk-{index}"
            else:  # is a non pass by ref, so just get the value itself
                return f"[@lstk-{index}]"
        else:
            debug(f"GETPASSVAR FAILED: {VarName}")
            raise ParseException(
                f"Attempt to access variable not in scope. Current function: {self.name}, variable: {VarName}")

    @property
    def num_params(self):
        return len(self.params)

    def assemble(self):
        # functions are jumped to with stack looking like: [ret, a, b, c]
        # we push lstk, then the function args
        yield f"_{self.name} NOP"
        # save previous base pointer [ret, a, b, c, lstk]
        yield "PUSH @LSTK"
        yield "MOV @STK @LSTK"  # copy current stack pointer to base pointer
        if self.vars_:
            for i in self.vars_:  # insert our function local vars
                yield from i.create()
        yield from self.assemble_list(self.children)
        yield "MOV 0 @RET"  # setup fall through return function
        yield "MOV @LSTK @STK"  # pull stack pointer back to base pointer
        # restore base pointer of previous function
        yield "MOV [@STK] @LSTK"
        yield "MOV @STK @ACC"
        yield f"ADD {self.num_params+1}"
        yield "MOV @ACC @STK"
        yield "RET"


class returnStmtOB(languageSyntaxOBbase):

    def __init__(self, returnVar):
        super().__init__(returnVar)
        self.returnVar = returnVar

    def assemble(self):
        """
        how to return:
            move returned variable to @RET
            move @LSTK to @STK (reset stack pointer)
            move [@LSTK] to @STK (return old pointer)
            add <number of vars> to @STK (push stack above pointer)
            call RET
        """
        if isinstance(self.returnVar, str):  # assume variable name
            yield f"MOV {self.get_variable(self.returnVar)} @RET"
        elif isinstance(self.returnVar, int):
            yield f"MOV {self.returnVar} @RET"
        elif isinstance(self.returnVar, listIndexOB):
            yield f"MOV [{self.returnVar.location}] @RET"
        yield "MOV @LSTK @STK"
        yield "MOV [@STK] @LSTK"
        yield "MOV @STK @ACC"
        yield f"ADD {self.num_params+1}"
        yield "MOV @ACC @STK"
        yield "RET"


class inlineAsmOB(languageSyntaxOBbase):

    def __init__(self, *asm):
        debug(f"asm = {asm}")
        super().__init__(asm)
        self.asm = asm

    def assemble(self):
        return self.asm


def wrapped_elem(wrapper, elem):
    wrap = pp.Literal(wrapper).suppress()
    return wrap + elem + wrap


class atoms:
    integer = pp.Word(pp.nums).setParseAction(lambda t: int(t[0]))
    variable = pp.Word(pp.alphas + "_", pp.alphanums + "_", exact=0)

    semicol = pp.Literal(";").suppress()
    equals = pp.Literal(":=").suppress()

    opening_curly_bracket = pp.Literal("{").suppress()
    closing_curly_bracket = pp.Literal("}").suppress()

    lparen = pp.Literal("(").suppress()
    rparen = pp.Literal(")").suppress()
    lsqrbrk = pp.Literal("[").suppress()
    rsqrbrk = pp.Literal("]").suppress()

    comma = pp.Literal(",").suppress()

    comparison = pp.oneOf("== != > < >= <=")

    addsub = pp.oneOf("+ -")
    muldiv = pp.oneOf("* /")

    oplist = [(muldiv, 2, pp.opAssoc.LEFT),
              (addsub, 2, pp.opAssoc.LEFT)]

    intvar = pp.Keyword("int") + variable  # ['int', name]
    listype = pp.Keyword("list") + variable
    listvar = (listype + lsqrbrk +
               pp.Optional(integer, default=None) + rsqrbrk)  # ['list', name, size]
    typedvar = listvar | intvar

    initTypedVar = (intvar | listype).setParseAction(lambda t: variableOB(*t))

    listindex = variable + lsqrbrk + (integer | variable) + rsqrbrk
    listindex.setParseAction(lambda t: listIndexOB(*t))

    # attempt to parse a listindex first, since otherwise a variable will be
    # parsed by mistake
    operand = listindex | integer | variable
    text = pp.Word(pp.alphanums + "_ $[]+-@\\")


class FuncCallSolver:
    functionCall = pp.Forward()
    arg = functionCall | atoms.operand
    args = arg + pp.ZeroOrMore(atoms.comma + arg)
    args.setParseAction(lambda t: varList(*t))

    functionCall << atoms.variable + atoms.lparen + \
        pp.Optional(args) + atoms.rparen
    functionCall.setParseAction(lambda s, l, t: functionCallOB(*t))

    functionCallInline = functionCall + atoms.semicol


class AssignmentSolver:
    operator = FuncCallSolver.functionCall | atoms.operand

    expr = pp.infixNotation(
        operator, atoms.oplist).setParseAction(lambda s, l, t: mathOP(t.asList()))

    assign = (atoms.listindex | atoms.variable) + atoms.equals + expr
    assignmentCall = assign + atoms.semicol
    assignmentCall.setParseAction(lambda s, l, t: assignOP(*t))


class returnStatement:

    returnStmnt = (pp.Keyword("return").suppress() +
                   atoms.operand + atoms.semicol).setParseAction(lambda t: returnStmtOB(*t))


class inlineAsm:

    asm = (pp.Keyword("_asm").suppress() + atoms.opening_curly_bracket +
           atoms.text + pp.ZeroOrMore(atoms.comma + atoms.text) +
           atoms.closing_curly_bracket()).setParseAction(lambda t: inlineAsmOB(*t))


class SyntaxBlockParser:

    program = AssignmentSolver.assignmentCall | FuncCallSolver.functionCallInline | returnStatement.returnStmnt | inlineAsm.asm
    syntaxBlock = pp.Forward()

    Syntaxblk = pp.OneOrMore(syntaxBlock | program)

    condition = atoms.lparen + atoms.operand + \
        atoms.comparison + atoms.operand + atoms.rparen
    condition.setParseAction(lambda s, l, t: comparisonOB(*t))

    blockTypes = pp.Keyword("if") | pp.Keyword("while")

    syntaxBlock << blockTypes + condition + \
        atoms.opening_curly_bracket + Syntaxblk + atoms.closing_curly_bracket
    syntaxBlock.setParseAction(
        lambda t: languageSyntaxOB(*t))


class OperationsObjects:

    SyntaxBlocks = SyntaxBlockParser.syntaxBlock
    assignBlocks = AssignmentSolver.assignmentCall
    functionCallBlocks = FuncCallSolver.functionCallInline
    statements = returnStatement.returnStmnt
    asm = inlineAsm.asm

    operation = SyntaxBlocks | assignBlocks | functionCallBlocks | statements | asm

    @classmethod
    def parse(cls, string):
        return cls.operation.parseString(string).asList()


class ProgramObjects:

    program = pp.Keyword("program").suppress() + atoms.opening_curly_bracket + \
        pp.OneOrMore(OperationsObjects.operation) + atoms.closing_curly_bracket
    program.setParseAction(lambda s, l, t: programList(*t))


class FunctionDefineParser:

    var_assign_line = atoms.typedvar + atoms.equals + (atoms.integer | wrapped_elem('"', atoms.text)) + atoms.semicol
    var_assign_line.setParseAction(lambda s, l, t: variableOB(*t))

    var_noassign_line = atoms.typedvar + atoms.semicol
    var_noassign_line.setParseAction(lambda s, l, t: variableOB(*t, 0))
    # init params that start with nothing to 0 with 0
    varline = var_assign_line | var_noassign_line
    varsblock = pp.Keyword("vars").suppress() + atoms.opening_curly_bracket + \
        pp.OneOrMore(varline) + atoms.closing_curly_bracket
    varsblock.setParseAction(lambda s, l, t: varList(*t))

    args = atoms.initTypedVar + \
        pp.ZeroOrMore(atoms.comma + atoms.initTypedVar)

    argblock = atoms.lparen + pp.Optional(args) + atoms.rparen
    argblock.setParseAction(lambda t: varList(*t))

    startblock = pp.Keyword("func").suppress() + atoms.variable + \
        argblock + atoms.opening_curly_bracket

    function = startblock + \
        pp.Optional(varsblock, default=None) + \
        ProgramObjects.program + atoms.closing_curly_bracket
    function.setParseAction(lambda s, l, t: functionDefineOB(*t))

    @classmethod
    def parse(cls, string):
        return cls.function.parseString(string).asList()


class ProgramSolver:

    functions = pp.OneOrMore(FunctionDefineParser.function)

    @classmethod
    def parse(cls, string):
        return cls.functions.parseString(string).asList()


def load_parse(fname):
    with open(fname) as f:
        program = f.read()
        functions = ProgramSolver.parse(program)  # .strip("\n"))

        compiled = ["call main", "halt"]
        debug(f"functions = {functions}")
        for i in functions:
            i.parent_own_children()
            print(format_string(str(i)))
            compiled += i.assemble()

            with open(f"{fname}.compiled", "w+") as f:
                f.writelines("\n".join(compiled))


if __name__ == "__main__":
    import sys
    for i in sys.argv[1:]:
        print(f"compiling {i}")
        load_parse(i)
