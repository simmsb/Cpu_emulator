import pyparsing as pp


class cmp:

    cmp_map = {
        "==": "eq"
    }  # TODO: complete

    def __init__(self, object):
        self.comp

semicol = pp.Literal(";").suppress()
equals = pp.Literal(":=").suppress()

opening_curly_bracket = pp.Literal("{").suppress()
closing_curly_bracket = pp.Literal("}").suppress()

lparen = pp.Literal("(").suppress()
rparen = pp.Literal(")").suppress()
comma = pp.Literal(",").suppress()

comparison = pp.oneOf("== != > < >= <=")
