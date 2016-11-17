from .opcodes import *
from .memory import *


class Registers:

    def __init__(self):
        self.register_map = {
            "cur": 0,  # current instruction
            "acc": 1,  # accumulator
            "rax": 2,  # function return
            "eax": 3,  # general purpose
            "ret": 4,  # function return to
            "cmp": 5,  # last comparison [L, M, Le, Me, Eq, L0, M0, Eq0]
        }
        self.register_memory = [0 for i in range(len(self.register_map) - 1)]
        self.register_memory.append('00000')

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
        n = max(1, n)
        return [string[i:i + n] for i in range(0, len(string), n)]

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
                self.registers["cur"] += 1  # increment counter
                self.decode_numeric_command(instruction)
            except CpuStoppedCall:
                break


class Compiler:
    # Todo: add ability to compile program into a list of functors

    def __init__(self, program_string, memory_size):
        self.program = [i for i in program_string.split('\n')] if \
        isinstance(program_string, str) else program_string
        # allow both string of commands and list of commands
        self.instruction_set = InstructionSet()
        self.memory_size = memory_size
        self.labels = {}
        self.named_jumps = {}
        self.compiled = []

    def preprocess(self, commands):
        label_counter = 1  # leave room for jump at start
        temporary_commands = commands.copy()
        return_commands = []

        for i, c in enumerate(commands):  # remove variables
            split = c.split()
            op = split[0]
            if not self.instruction_set.encode_name(op):  # is a label
                if not op.startswith("_"):  # is a variable
                    self.labels[op] = str(label_counter)
                    temporary_commands[i] = split[1] if len(split) > 1 else 0
                    label_counter += 1

        print(temporary_commands)

        for i, c in enumerate(temporary_commands):  # generate jumps
            split = c.split()
            op = split[0]
            if not self.instruction_set.encode_name(op):  # is a jump
                if op.startswith("_"):  # is a jump
                    self.named_jumps[op[1:]] = "#{}".format(str(i + 1))
                    temporary_commands[i] = " ".join(split[1:])

        print(temporary_commands)

        for i in temporary_commands:
            split = i.split()
            op = split[0]  # type: str
            if self.instruction_set.encode_name(op):  # is a command
                print(split)
                temp = i
                for k, j in self.labels.items():
                    temp = temp.replace(k, j)
                for k, j in self.named_jumps.items():
                    temp = temp.replace(k, j)
                return_commands.append(temp)
            elif op.isdigit():
                # if it is a number, keep it anyway
                return_commands.append(int(op))

        return_commands.insert(0, "jump #{}".format(len(self.labels) + 1))

        return return_commands

    def compile_command(self, command_str):
        if isinstance(command_str, int):
            return command_str  # if just a number, keep it
        keys = command_str.split()
        command = self.instruction_set.encode_name(keys[0])
        operstring = ' '.join(keys[1:])
        if command:  # command exists
            operands = ''.join([str(ord(k)).zfill(8) for k in operstring])
            return int(str(command) + operands)
        else:
            raise Exception

    def compile(self):
        self.program = self.preprocess(self.program)
        print("Program = {}".format(self.program))
        for c, i in enumerate(self.program):
            try:
                self.compiled.append(self.compile_command(i))
            except:
                raise Exception(
                    "Invalid command passed: ({}) on line {}".format(i, c))
