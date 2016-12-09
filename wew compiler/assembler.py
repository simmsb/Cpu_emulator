import re


"""
Idea of this:

every line gets placed into a BaseSyntax object.

then each syntax object is iterated over until there are no non parsed code left.

then from the roots the syntax is compiled into the assembly

before finally being placed
"""


class SyntaxException(Exception):
    pass


class BaseSyntax:
    """Base syntax object for holding syntax"""

    @classmethod
    def recognise(cls, string):
        return cls, 0, len(string)

    def __init__(self, syntax_block, parent=None):
        self.parent = parent
        self.syntax_block = syntax_block
        self.children = []
        if self.parent:
            parent.initialize_child(self)

    def initialize_child(self, child):
        self.children.append(child)

    def __str__(self):
        return "Empty syntax object"


class ProgramSyntax(BaseSyntax):

    @classmethod
    def recognise(cls, string):
        startPos, endPos = None, None

        start = re.compile("PROGRAM\ .+")
        end = re.compile("ENDPROGRAM")

        for c, i in enumerate(string):
            if start.match(i):
                if startPos is None:
                    program_name = i.split()[-1]
                    startPos = c
                else:
                    raise SyntaxException(
                        "Multiple PROGRAM initiators, second on line: {}".format(c))
            if end.match(i):
                if endPos is None and startPos is None:
                    endPos = c
                else:
                    raise SyntaxException(
                        "Multiple PROGRAM terminators or mismatched initiator/ terminators, second on line: {}".format(c))

        return cls, startPos, endPos

    def __str__(self):
        # this is how we will generate the compiled object
        return "call main\nhalt\n{}".format("{}\n".join([str(i) for i in self.children]))


class FunctionSyntax(BaseSyntax):

    @classmethod
    def recognise(cls, string):
        startPos, endPos = None, None

        start = re.compile("FUNCTION\ .+")
        end = re.compile("ENDFUNCTION")

        for c, i in enumerate(string):
            if start.match(i):
                if startPos is None:
                    program_name = i.split()[-1]
                    startPos = c
                else:
                    raise SyntaxException(
                        "Multiple FUNCTION initiators, second on line: {}".format(c))
            if end.match(i):
                if endPos is None and startPos is None:
                    endPos = c
                else:
                    raise SyntaxException(
                        "Multiple FUNCTION terminators or mismatched initiator/ terminators, second on line: {}".format(c))

        return cls, startPos, endPos

    def __init__(self, syntax_block, parent=None):
        super().__init__(syntax_block, parent)
        self.name = syntax_block[0].split()[1]
        self.passed_variables = syntax_block[0].split()[2:]
        self.syntax_block = syntax_block[1:-1]
        self.define_variables = self.find_vars()

    def find_vars(self):
        varstart = None
        varend = None
        for c, i in enumerate(self.syntax_block):
            if i.strip().lower() == "vars":
                varstart = c+1
            elif i.strip().lower() == "BEGIN":
                varend = c-1

        return filter(None, self.syntax_block[varstart, varend])
