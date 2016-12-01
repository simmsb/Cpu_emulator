import re

from .memory import *
from .opcodes import *

DEBUG = False


class Registers:
    """Object that holds the registers for the computer

    Has getitem and setitem overrides, so can be treated like a dictionary containing the registers

    Arguments
    ---------

    memory_size: <int> Size of memory the cpu is given
    """

    def __init__(self, memory_size):
        self.registers = {
            "cur": 0,  # current instruction
            "acc": 0,  # accumulator
            "rax": 0,  # function return
            "eax": 0,  # general purpose
            "ret": 0,  # function return to
            "stk": memory_size,  # current stack position, start at last memory position
            # last comparison [less, more, less equal, more equal equal]
            "cmp": '00000'
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
    """CPU that links instructions, memory and registers together

    Arguments
    ---------

    memory_capacity: <int> base length of program

    program: <iterator> Iterator/ list of instructions to load memory with


    functions
    ---------

    execute(): Begin execution of program"""

    def __init__(self, memory_capacity, program=None):
        super().__init__()
        self.memory = Memory(memory_capacity, 0)
        if program:
            self.memory.load_program(program)
        self.registers = Registers(self.memory.size)
        self.instruction_set = InstructionSet(self)

    @staticmethod
    def _split_every(string, n):
        n = max(1, n)
        return [string[i:i + n] for i in range(0, len(string), n)]

    def _decode_numeric_command(self, value):
        if value is 0:
            raise CpuStoppedCall("CPU halted: no command")
            # empty memory address, stop here
        try:
            opcode = int(str(value)[:3])
            split_codes = self._split_every(str(value)[3:], 8)
            operands = ''.join([chr(int(i)) for i in split_codes]).split()
            if DEBUG:
                print("Opcode was: {}".format(opcode))
                print("Operands were: {}".format(operands))
            self.instruction_set.run_encoded(opcode, *operands)
        except CpuStoppedCall as e:
            raise e  # re-raise here so we can ignore it
        except Exception as e:
            print("Computer crashed!")
            print("Last instruction was: {}".format(
                self.instruction_set.encoded_commands[opcode].__name__))
            print("operands were: {}".format(operands))
            print("exception was: {}".format(e))
            raise CpuStoppedCall("Computer Crashed Halt")

    def interpret_address(self, string):
        """#3 for immediate
        @reg for register
        3 for memory_location"""
        string = str(string)

        in_place_add = re.compile("(?!\[)([^\[\]]+)[+-]([^\[\]]+)(?=\])")  # allow for in-place addition/ subtraction
        function_match = re.compile("(?![^+-])[+=](?=[^+-])")

        function_map = {
            "+":(lambda a, b:interpret(a)+interpret(b)),
            "-":(lambda a, b:interpret(a)-interpret(b))
        }

        def interpret_memory_location(location_string):
            return self.registers[location_string.lstrip("@")] if location_string.startswith("@") else \
                self.memory[int(location_string)]

        def interpret(location_string):
            return int(location_string.lstrip("#")) if location_string.startswith("#") else interpret_memory_location(location_string)

        multiples = in_place_add.search(string)
        if multiples:
            return function_map[function_match.search(multiples.group()).group()](*re.split(r"[+=]", multiples.group()))
        else:
            return interpret(string)






    def execute(self):
        while True:
            try:
                current_instruction = self.memory[self.registers["cur"]]
                self.registers["cur"] += 1  # increment counter
                self._decode_numeric_command(current_instruction)
            except CpuStoppedCall as e:
                print(e)
                break


class Compiler:
    """Object that compiles a program for an instruction set

    Arguments
    ---------

    program_string: <List> or newline seperated string of instructions

    memory_size: <int> size of memory cells to give the program


    Functions
    ---------

    compiled: returns map object of compiled commands"""

    def __init__(self, program_string, memory_size):
        self.program = [i for i in program_string.split('\n')] if \
            isinstance(program_string, str) else program_string
        # allow both string of commands and list of commands
        self.instruction_set = InstructionSet()
        self.memory_size = memory_size

    @staticmethod
    def _replace_with_spaces(string, search, replace):
        """Replace individual words, no fuzzyness"""
        return " ".join([replace if i == search else i for i in string.split()])

    def _pre_process_instructions(self, commands):
        return_commands = list()
        labels = dict()
        named_jumps = dict()
        label_values = list()

        def _comment_empty_filter(line):
            """Remove comments and empty lines
            returns None if line ended up being empty"""
            return line.split(";")[0].rstrip() or None

        temporary_commands = list(
            filter(None, map(_comment_empty_filter, commands)))
        label_commands = temporary_commands.copy()
        # remove constant variables and empty lines
        for i, c in enumerate(label_commands):
            split = c.split()
            op = split[0]

            if not self.instruction_set.encode_name(op) and not op.startswith("_"):
                labels[op] = len(labels)  # next value is always
                label_values.append(int(split[1]) if len(split) > 1 else 0)
                temporary_commands.remove(c)  # cut from list

        for i, c in enumerate(temporary_commands):  # generate jumps
            split = c.split()
            op = split[0]
            if not self.instruction_set.encode_name(op):  # is a jump
                if op.startswith("_"):  # is a jump
                    named_jumps[op[1:]] = "#{}".format(str(i))
                    temporary_commands[i] = " ".join(split[1:])

        program_length = len(temporary_commands)

        for i in temporary_commands:
            split = i.split()
            op = split[0]  # type: str
            if self.instruction_set.encode_name(op):  # is a command
                temp = i
                for k, j in labels.items():
                    temp = self._replace_with_spaces(
                        temp, k, str(program_length + j))
                for k, j in named_jumps.items():
                    temp = self._replace_with_spaces(temp, k, j)
                return_commands.append(temp)
            elif op.isdigit():
                # if it is a number, keep it anyway
                return_commands.append(int(op))
        for i in label_values:
            # add initialised variable to end of program
            return_commands.append(i)
        return return_commands

    def _compile_command(self, command_str):
        if isinstance(command_str, int):
            return command_str  # if just a number, keep it
        keys = command_str.split()
        command = self.instruction_set.encode_name(keys[0])
        if command:  # command exists
            operstring = ' '.join(keys[1:])
            operands = ''.join([str(ord(k)).zfill(8) for k in operstring])
            return int(str(command) + operands)
        else:
            raise Exception

    @property
    def compiled(self):
        processed = self._pre_process_instructions(self.program)
        return map(self._compile_command, processed)
