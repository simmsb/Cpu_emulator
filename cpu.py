class MemoryOverFlowException(Exception):
    pass

class CpuStoppedCall(Exception):
    pass

class Memory:
    def __init__(self, size, default):
        self.cells = [default for i in range(size)]

    def load_program(self, program):
        self.cells = program + self.cells

    def __getitem__(self, key):
        if len(self.cells) < key:
            raise MemoryOverFlowException("SEGFAULT: Attemt to access memory",
                            " location outside of physical capacity (Address: {})".format(key))
        else:
            return self.cells[key]

    def __setitem__(self, key, value):
        if len(self.cells) < key:
            raise MemoryOverFlowException("SEGFAULT: Attemt to set memory",
                        " location outside of physical capacity (Address: {})".format(key))
        else:
            self.cells[key] = value

    def __delitem__(self, key):
        if len(self.cells) < key:
            raise MemoryOverFlowException("SEGFAULT: Attemt to set memory",
                        " location outside of physical capacity (Address: {})".format(key))
        else:
            self.cells[key] = 0


instruction_map = {}
instruction_names = {}
def instruction(numerical):
    def decorator(func):
        instruction_map[numerical] = func
        instruction_names[func.__name__] = numerical
        return func
    return decorator

class InstructionSet:

    def __init__(self):
        self.encoded_commands = instruction_map.copy()
        self.instruction_names = instruction_names.copy()

    def run_encoded(self, command, *args):
        command = self.encoded_commands.get(command)
        if command:
            print("calling command: {0.__name__} with args: {1}".format(command, args))
            command(self, *args)
        else:
            raise CpuStoppedCall("Invalid command/ Halt Raised")

    def encode_name(self, command_name):
        return self.instruction_names.get(command_name)

    @instruction(111)
    def add(self, value):
        self.registers["acc"] += self.interpret_address(value)

    @instruction(112)
    def sub(self, value):
        self.registers["acc"] += self.interpret_address(value)

    @instruction(113)
    def mul(self, value):
        self.registers["acc"] += self.interpret_address(value)

    @instruction(114)
    def sub(self, value):
        self.registers["acc"] += self.interpret_address(value)

    @instruction(115)
    def set(self, value):
        self.registers["acc"] += self.interpret_address(value)

    @instruction(116)
    def mov(self, from_loc, to_loc):
        # move from register to location
        if to_loc.startswith("@"):
            self.registers[to_loc.lstrip("@")] = self.interpret_address(from_loc)
        else:
            self.memory[int(to_loc)] = self.interpret_address(from_loc)

    @instruction(117)
    def cmp(self, a, b=0):
        functions = [
            (lambda a, b: a < b),
            (lambda a, b: a > b),
            (lambda a, b: a <= b),
            (lambda a, b: a >= b),
            (lambda a, b: a == b),
            (lambda a, b: a < 0),
            (lambda a, b: a > 0),
            (lambda a, b: a == 0)
        ]
        self.registers["cmp"] = sum([functions[i](a,b)*(2**i) for i in range(0, len(functions))])

    @instruction(118)
    def jump(self, jump):
        self.registers["cur"] = self.interpret_address(jump)

    @instruction(119)
    def _test_cmp(self, index):
        return bin(self.registers["cur"])[:1:-1][index]

    @instruction(120)
    def lje(self, jump): # less than
        if self._test_cmp(0):
            self.jump(jump)

    @instruction(121)
    def mje(self, jump): # less than
        if self._test_cmp(1):
            self.jump(jump)

    @instruction(122)
    def leje(self, jump): # less than
        if self._test_cmp(2):
            self.jump(jump)

    @instruction(123)
    def meje(self, jump): # less than
        if self._test_cmp(3):
            self.jump(jump)

    @instruction(124)
    def eqje(self, jump): # less than
        if self._test_cmp(4):
            self.jump(jump)

    @instruction(125)
    def lzje(self, jump): # less than
        if self._test_cmp(5):
            self.jump(jump)

    @instruction(126)
    def mzje(self, jump): # less than
        if self._test_cmp(6):
            self.jump(jump)

    @instruction(127)
    def eqzje(self, jump): # less than
        if self._test_cmp(7):
            self.jump(jump)

    @instruction(128)
    def prntint(self, memoc):
        print(self.interpret_address(memloc))

    @instruction(129)
    def prntstr(self, memloc):
        print(chr(self.interpret_address(memloc)))

class Registers:
    def __init__(self):
        self.register_memory = [0 for i in range(5)]
        self.register_map = {
            "cur": 0,  # current instruction
            "acc":1,  # accumulator
            "rax":2,  # function return
            "eax":3,  # general purpose
            "ret":4,  # function return to
            "cmp":5,  # last comparison [L, M, Le, Me, Eq, L0, M0, Eq0]
            }

    def __getitem__(self, key):
        return self.register_memory[self.register_map[key]]

    def __setitem__(self, key, value):
        self.register_memory[self.register_map[key]] = value


class Cpu(InstructionSet):
    def __init__(self, memory_capacity, program=[]):
        super().__init__()
        self.memory = Memory(memory_capacity, 0)
        if program:
            self.memory.load_program(program)
        self.registers = Registers()

    def decode_string_command(self, string):
        codes = string.lower().split()
        opcode = codes.pop(0)
        self.execute_command(opcode, *codes)

    def split_every(self, string, n):
        n = max(1,n)
        return [string[i:i+n] for i in range(0, len(string), n)]

    def decode_numeric_command(self, value):
        opcode = int(str(value)[:3])
        split_codes = self.split_every(str(value)[3:], 8)
        operands = ''.join([chr(int(i)) for i in split_codes]).split()
        self.run_encoded(opcode, *operands)

    def execute_command(self, opcode, *codes):
        command = self.__getattribute__(opcode)
        command(*codes)

    def interpret_address(self, string):
        '''#3 for immediate
        @reg for register
        3 for memory_location'''
        def interpret_memory_location(string):
            return self.registers[string.lstrip("@")] if string.startswith("@") else self.memory[int(string)]

        return int(string.lstrip("#")) if string.startswith("#") else interpret_memory_location(string)


    def execute(self):
        while True:
            try:
                instruction = self.memory[self.registers["cur"]]
                self.registers["cur"] += 1 # increment counter
                self.decode_numeric_command(instruction)
            except CpuStoppedCall:
                break

class Compiler:
    # Todo: add ability to compile program into a list of functors
    def __init__(self, program_string):
        self.program = [i for i in program_string.split('\n')]
        self.instruction_set = InstructionSet()
        self.labels = {}
        self.compiled = []


    def preprocess(self, commands):
        label_counter = 1 # leave room for jump at start
        for c, i in enumerate(commands):
            if not i:
                pass
            split = i.split()
            print(split)
            op = split[0]
            if not self.instruction_set.encode_name(op):  # is a label
                val = int(split[1])
                self.labels[op] = str(label_counter)
                self.program[label_counter] = val
                self.program.pop(c)
                label_counter += 1
                # increment number of labels in use

    def compile(self):
        self.preprocess(self.program)
        self.program.insert(0, "jump {}".format(len(self.labels)))
        print(self.program)
        for i in self.program:
            print(i)
            keys = i.split()
            command = self.instruction_set.encode_name(keys[0])
            operstring = ' '.join(keys[1:])
            for label, memloc in self.labels.items():
                operstring.replace(label, memloc)  # replace labels with memory locations
            if command:  # command exists
                operands = ''.join([str(ord(k)).zfill(8) for k in operstring])
                self.compiled.append(int(str(command)+operands))

command = '''counter 5
mov counter @acc
mul 5
mov @acc counter
prntint counter'''

myprogram = Compiler(command)
myprogram.compile()

mycpu = Cpu(400, myprogram.compiled)
# Todo: add interpretation of assembly file
