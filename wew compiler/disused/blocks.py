import pyparsing as pp

import atoms
import tokens


class function_definition:
    funcstruct = pp.Forward()  # create here since func calls can have func calls

    func_arg = funcstruct | atoms.operand
    arg_chain = func_arg + pp.ZeroOrMore(tokens.comma + func_arg)

    # TODO: complete
