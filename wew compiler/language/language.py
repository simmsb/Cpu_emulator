import re


"""
Idea of this:

every line gets placed into a BaseSyntax object.

then each syntax object is iterated over until there are no non parsed code left.

then from the roots the syntax is compiled into the assembly

before finally being placed
"""

syntax_objects = []

def syntax_object():
    def deco(Klass):
        syntax_object.append(Klass)
        return Klass
    return deco


class SyntaxException(Exception):
    pass


class BaseSyntax:
    """Base syntax object for holding syntax"""

    @classmethod
    def recognise(cls, string):
        return cls, 0, len(string)


    def __init__(self, parent=None, syntax_block):
        self.parent = parent
        self.syntax_block = syntax_block
        self.children = []
        if self.parent:
            parent.initialize_child(self)


    def initialize_child(self, child):
        self.children.append(child)


    def __str__(self):
        return "Empty syntax object"


@syntax_object()
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
                    raise SyntaxException("Multiple PROGRAM initiators, second on line: {}".format(c))
            if end.match(i):
                if endPos is None:
                    endPos = c
                else:
                    raise SyntaxException("Multiple PROGRAM terminators, second on line: {}".format(c))

        return cls, startPos, endPos


    def __str__(self):
        return "call main\nhalt\n{}".format("{}\n".join([str(i) for i in self.children])) # this is how we will generate the compiled object
