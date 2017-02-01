import pyparsing as pp


class Atom:

    def __init__(self, object):
        self.object = object


integer = pp.Word(pp.nums).setParseAction(lambda t: Atom(int(t[0])))
variable = pp.Word(pp.alphas + "_", pp.alphanums +
                   "_", exact=0).setParseAction(lambda t: Atom(*t))
operand = integer | variable


class operators:

    class Operator:

        def __init__(self, object):
            self.object = object

    plus = pp.Literal("+")
    sub = pp.Literal("-")
    div = pp.Literal("/")
    mul = pp.Literal("*")

    lshift = pp.Literal("<<")
    rshift = pp.Literal(">>")

    op = (plus | sub | div | mul | lshift |
          rshift).setParseAction(lambda t: Operator(*t))
