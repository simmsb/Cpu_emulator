class CpuStoppedCall(Exception):
    pass

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
            '''print("calling command: {0.__name__} with args: {1}".format(
                command, args))'''
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
        self.registers["acc"] -= self.interpret_address(value)

    @instruction(113)
    def mul(self, value):
        self.registers["acc"] *= self.interpret_address(value)

    @instruction(114)
    def sub(self, value):
        self.registers["acc"] -= self.interpret_address(value)

    @instruction(115)
    def set(self, value):
        self.registers["acc"] = self.interpret_address(value)

    @instruction(116)
    def mov(self, from_loc, to_loc):
        # move from register to location
        if to_loc.startswith("@"):
            self.registers[to_loc.lstrip(
                "@")] = self.interpret_address(from_loc)
        else:
            self.memory[int(to_loc)] = self.interpret_address(from_loc)

    @instruction(117)
    def cmp(self, a, b=0):
        av = self.interpret_address(a)
        # print("comp interpreted as {}".format(av))
        bv = self.interpret_address(b) if b else 0
        functions = [
            (lambda a, b: a < b),
            (lambda a, b: a > b),
            (lambda a, b: a <= b),
            (lambda a, b: a >= b),
            (lambda a, b: a == b)
        ]
        self.registers["cmp"] = "".join(
            [str(1 if i(av, bv) else 0) for i in functions])

    @instruction(118)
    def jump(self, jump):
        self.registers["cur"] = self.interpret_address(jump)

    @instruction(119)
    def _test_cmp(self, index):
        return int(self.registers["cmp"][index])

    @instruction(120)
    def lje(self, jump):  # less than
        if self._test_cmp(0):
            self.jump(jump)

    @instruction(121)
    def mje(self, jump):  # more than
        if self._test_cmp(1):
            self.jump(jump)

    @instruction(122)
    def leje(self, jump):  # less than equal
        if self._test_cmp(2):
            self.jump(jump)

    @instruction(123)
    def meje(self, jump):  # more than equal
        if self._test_cmp(3):
            self.jump(jump)

    @instruction(124)
    def eqje(self, jump):  # equal
        if self._test_cmp(4):
            self.jump(jump)

    @instruction(128)
    def prntint(self, memloc):
        print(self.interpret_address(memloc))

    @instruction(129)
    def prntstr(self, memloc):
        print(chr(self.interpret_address(memloc)))

    @instruction(130)
    def input(self, memloc):
        if memloc.startswith("@"):
            self.registers[memloc.strip("@").lower()] = int(
                input("Enter number: "))
        else:
            self.memory[int(memloc)] = int(input("Enter number: "))

    @instruction(131)
    def halt(self):
        raise CpuStoppedCall("HALT command ran")
