
import lexer


jump_counter = 0


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
        n = statement.split()
        self.a = n[0]
        self.comparison = n[1]
        self.b = n[2]
        self.code = code
        self.parsed_code = ""

    def evaluate(self):
        start = "_loop{0} cmp {1.a} {1.b}\n{2} loopend{0}\n".format(jump_counter, self)
        end = "_loopend{0} nop".format(jump_counter)
        jump_counter += 1



class FunctionObject:
    def __init__(self, name, params, code):
        self.name = name
        self.params = params
        self.vars = []
        self.code = code
        self.parsed_code = []
        self.parse_vars()

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
        self.code = self.code[h+1:]


    def evaluate(self):





def parse(program_list):

    def except_whitespace(program_list):
        print(list(filter(None, map(lambda x: x.strip(), program_list))))
        return list(filter(None, map(lambda x: x.strip(), program_list)))

    def parse_functions(program_list):
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
                        functions.append(FunctionObject(fdata[0], fdata[1:], program_list[i+1: h]))
                        i = h
                        break
            i += 1

        return functions
    return parse_functions(except_whitespace(program_list))



def load_file(fname):
    with open(fname) as file:
        return file.read().split("\n")
