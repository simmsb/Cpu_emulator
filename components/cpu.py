from .opcodes import *
from .memory import *


DEBUG = False


class Registers:

    def __init__(self, mem_size):
        self.registers = {
            "cur": 0,  # current instruction
            "acc": 0,  # accumulator
            "rax": 0,  # function return
            "eax": 0,  # general purpose
            "ret": 0,  # function return to
            "stk": mem_size-1,  # current stack position, start at last memory position
            "cmp": '00000'  # last comparison [L, M, Le, Me, Eq, L0, M0, Eq0]
        }

    def __getitem__(self, key):
        if self.registers.get(key) is None:
            raise CpuStoppedCall("Attemt to access nonexistant register")
        return self.registers.get(key)

    def __setitem__(self, key, value):
        if self.registers.get(key) is not None:
            self.registers[key] = value
        else:
            raise CpuStoppedCall("Attemt to access nonexistant register")


class Cpu:

    def __init__(self, memory_capacity, program=[]):
        super().__init__()
        self.memory = Memory(memory_capacity, 0)
        if program:
            self.memory.load_program(program)
        self.registers = Registers(self.memory.size)
        self.instruction_set = InstructionSet(self)

    def split_every(self, string, n):
        n = max(1, n)
        return [string[i:i + n] for i in range(0, len(string), n)]

    def decode_numeric_command(self, value):
        if value is 0:
            raise CpuStoppedCall("CPU halted: no command")
            # empty memory address, stop here
        opcode = int(str(value)[:3])
        split_codes = self.split_every(str(value)[3:], 8)
        operands = ''.join([chr(int(i)) for i in split_codes]).split()
        if DEBUG:
            print("Opcode was: {}".format(opcode))
            print("Operands were: {}".format(operands))
        self.instruction_set.run_encoded(opcode, *operands)

    def interpret_address(self, string):
        '''#3 for immediate
        @reg for register
        3 for memory_location'''
        string = str(string)
        def interpret_memory_location(string):
            return self.registers[string.lstrip("@")] if string.startswith("@") else self.memory[int(string)]

        return int(string.lstrip("#")) if string.startswith("#") else interpret_memory_location(string)

    def execute(self):
        while True:
            try:
                instruction = self.memory[self.registers["cur"]]
                self.registers["cur"] += 1  # increment counter
                self.decode_numeric_command(instruction)
            except CpuStoppedCall as e:
                print(e)
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

    @staticmethod
    def replace_with_spaces(string, search, replace):
        return " ".join([ replace if i == search else i for i in string.split()])

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
                    temporary_commands.remove(c)  # cut from list
                    temporary_commands.insert(label_counter-1, split[1] if len(split) > 1 else 0)  # always move to front
                    label_counter += 1

        for i, c in enumerate(temporary_commands):  # generate jumps
            split = c.split()
            op = split[0]
            if not self.instruction_set.encode_name(op):  # is a jump
                if op.startswith("_"):  # is a jump
                    self.named_jumps[op[1:]] = "#{}".format(str(i + 1))
                    temporary_commands[i] = " ".join(split[1:])


        for i in temporary_commands:
            split = i.split()
            op = split[0]  # type: str
            if self.instruction_set.encode_name(op):  # is a command
                temp = i
                for k, j in self.labels.items():
                    temp = self.replace_with_spaces(temp, k, j)
                for k, j in self.named_jumps.items():
                    temp = self.replace_with_spaces(temp, k, j)
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
