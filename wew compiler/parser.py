import lexer

jump_counter = 0


class CodeObject:

    def __init__(self, code, parent):
        self.code = code
        self.parent = parent

    @property
    def parsed_code(self):
        return None  # TODO: have this work


class WhileObject:

    compdict = {
        "<=": "mje",
        ">=": "lje",
        "<": "meje",
        ">": "leje",
        "!=": "eqje",
        "==": "nqje"
    }

    def __init__(self, statement, code):
        self.code = CodeObject(code, self)
        n = statement.split()
        self.a = n[0]
        self.comparison = n[1]
        self.b = n[2]

    def evaluate(self):
        start = "_loop{0} cmp {1.a} {1.b}\n{2} loopend{0}".format(
            jump_counter, self, self.compdict[self.comparison])
        end = "_loopend{0} nop".format(jump_counter)
        jump_counter += 1
        return start, self.code.parsed_code, end


class FunctionObject:

    def __init__(self, name, params, code):
        self.code = CodeObject(code, self)
        self.name = name
        self.params = params
        self.vars = []
        self.returns = []
        self.parse_vars()
        self.parse_returns()

    def parse_vars(self):
        i, h = 0, 0
        realcode = None
        while True:
            if self.code[i].startswith("VARS"):
                h = i
                while not self.code[h].startswith("BEGIN"):
                    h += 1
                    self.vars.append(self.code[h])
                break

        self.vars = self.vars[:-1]
        self.code = self.code[h + 1:]

    def parse_returns(self):
        for i in self.code:
            if i.startswith("RETURN"):
                self.returns.append(
                    "mov {} @ret\n{}\nret".format(i.split()[-1], ))

    @property
    def parsed_vars(self):
        return ["pushstk #{}".format(i.split()[-1]) for i in self.vars]

    def getStackPosition(self, var):
        if var in self.params:
            # params are pushed on left to right, rightmost is at bottom
            return "[@lstk+{}]".format(self.params[::-1].index(var) + 1)
            #  reverse vars [a, b, c, d] -> [d, c, b, a] and get index + 1
        elif var in self.vars:
            # unlike params, stack pointer resides on last variable, not
            # previous stack
            return "@stk+{}".format(self.vars[::-1].index(var))

    def evaluate(self):
        # push current stack value onto stack, then copy stk to lstk, so lstk
        # resides on the old stack
        initiate_code = "pushstk @stk\nmov @stk @lstk"
        varinit = self.parsed_vars
        deconstructor = "mov #0 @ret\nmov [@lstk] @stk\n{}".format("\n".join(
            "popstk" for i in self.params))  # copy last stack position onto stack, then pop parameters off
        # also sets return to 0 since we might be a procedure and not supposed
        # to return anything
        start = "_{} nop"
        end = "ret"  # return at end of function

        return start, initiate_code, varinit, self.code.parsed_code, deconstructor, end


def parse_function(program_list):

    def except_whitespace(program_list):
        return list(filter(None, map(lambda x: x.strip(), program_list)))

    def parse(program_list):
        i = 0
        functions = []
        while i < len(program_list):
            print(i)
            if program_list[i].startswith("FUNCTION"):
                h = i
                while True:
                    h += 1
                    if program_list[h].startswith("ENDFUNCTION"):
                        fdata = program_list[i].split()[1:]
                        functions.append(FunctionObject(
                            fdata[0], fdata[1:], program_list[i + 1: h]))
                        i = h
                        break
            i += 1

        return functions
    return parse(except_whitespace(program_list))


def load_file(fname):
    with open(fname) as file:
        return file.read().split("\n")
