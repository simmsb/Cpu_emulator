# [['a', '+', ['b', '/', 'c', '*', 2], '-', <__main__.mathop object at 0x03694870>]]
import operator

from .lexer import mathop

op_map = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv
}

asm_map = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV"
}


class no_depth_list(list):
    """Class that does not allow any nested lists to be appended, any iterables appended will be unpacked first """

    def __lshift__(self, other):
        self.append(other)


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


def stack_to_ops(stack):
    out = no_depth_list()
    for i in stack:
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
            for i in self.assemble_list(i):
                out << i
            out << "PUSHSTK @RET"


if __name__ == "__main__":
    print(parse([['a', '+', ['b', '/', 'c', '*', 2], '-', 4]]))
