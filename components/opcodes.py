class CpuStoppedCall(Exception):
    pass

instruction_map = {}
instruction_names = {}


def instruction():
    def decorator(func):
        number = 110 + len(instruction_map)
        instruction_map[number] = func
        instruction_names[func.__name__] = number
        return func
    return decorator


class InstructionSet:

    def __init__(self, cpu=None):  # no cpu needed for compiler
        self.encoded_commands = instruction_map.copy()
        self.instruction_names = instruction_names.copy()
        self.cpu = cpu

    def run_encoded(self, command, *args):
        command = self.encoded_commands.get(command)
        if command:
            '''print("calling command: {0.__name__} with args: {1}".format(
                command, args))'''
            command(self, *args)
        else:
            raise CpuStoppedCall(
                "Invalid command entered, ID was: {}. Arguments were: {}".format(command, args))

    def encode_name(self, command_name):
        return self.instruction_names.get(command_name)

    @instruction()
    def add(self, value):
        self.cpu.registers["acc"] += self.cpu.interpret_address(value)

    @instruction()
    def sub(self, value):
        self.cpu.registers["acc"] -= self.cpu.interpret_address(value)

    @instruction()
    def mul(self, value):
        self.cpu.registers["acc"] *= self.cpu.interpret_address(value)

    @instruction()
    def div(self, value):
        self.cpu.registers["acc"] /= self.cpu.interpret_address(value)

    @instruction()
    def set(self, value):
        self.cpu.registers["acc"] = self.cpu.interpret_address(value)

    @instruction()
    def mov(self, from_loc, to_loc):
        if to_loc.startswith("@"):
            self.cpu.registers[to_loc.lstrip(
                "@")] = self.cpu.interpret_address(from_loc)
        else:
            self.cpu.memory[int(to_loc)] = self.cpu.interpret_address(from_loc)

    @instruction()
    def cmp(self, a, b=0):
        av = self.cpu.interpret_address(a)
        # print("comp interpreted as {}".format(av))
        bv = self.cpu.interpret_address(b) if b else 0

        functions = [
            (lambda a, b: a < b),
            (lambda a, b: a > b),
            (lambda a, b: a <= b),
            (lambda a, b: a >= b),
            (lambda a, b: a == b)
        ]
        self.cpu.registers["cmp"] = "".join(
            [str(1 if i(av, bv) else 0) for i in functions])

    def internal_jump(self, location):  # jumps to memory address provided, no interpreting
        self.cpu.registers["cur"] = location

    @instruction()
    def jump(self, jump):
        self.internal_jump(self.cpu.interpret_address(jump))

    @instruction()
    def _test_cmp(self, index):
        return int(self.cpu.registers["cmp"][index])

    @instruction()
    def lje(self, jump):  # less than
        if self._test_cmp(0):
            self.jump(jump)

    @instruction()
    def mje(self, jump):  # more than
        if self._test_cmp(1):
            self.jump(jump)

    @instruction()
    def leje(self, jump):  # less than equal
        if self._test_cmp(2):
            self.jump(jump)

    @instruction()
    def meje(self, jump):  # more than equal
        if self._test_cmp(3):
            self.jump(jump)

    @instruction()
    def eqje(self, jump):  # equal
        if self._test_cmp(4):
            self.jump(jump)

    @instruction()
    def prntint(self, memloc):
        print(self.cpu.interpret_address(memloc))

    @instruction()
    def prntstr(self, memloc):
        print(chr(self.cpu.interpret_address(memloc)), end='')

    @instruction()
    def prntnl(self):
        print("\n")

    @instruction()
    def input(self, memloc):
        if memloc.startswith("@"):
            self.cpu.registers[memloc.strip("@").lower()] = int(
                input("Enter number: "))
        else:
            self.cpu.memory[int(memloc)] = int(input("Enter number: "))

    @instruction()
    def halt(self):
        raise CpuStoppedCall("CPU halt triggered")

    @instruction()
    def movloc(self, from_loc, to_loc):
        # move from location stored in location to location
        if to_loc.startswith("@"):
            self.cpu.registers[to_loc.lstrip("@")] = self.cpu.memory[
                self.cpu.interpret_address(from_loc)]
        else:
            self.cpu.memory[int(to_loc)] = self.cpu.memory[
                self.cpu.interpret_address(from_loc)]

    @instruction()
    def popstk(self, memloc):
        if self.cpu.registers["stk"] > self.cpu.memory.size:
            return 0  # assume everything above maximum address is 0
        if memloc.startswith("@"):
            self.cpu.registers[memloc.lstrip("@")] = self.cpu.memory[
                self.cpu.registers["stk"]]
        else:
            self.cpu.memory[int(memloc)] = self.cpu.memory[
                self.cpu.registers["stk"]]
        self.cpu.registers["stk"] += 1  # stack descends upwardas

    @instruction()
    def pushstk(self, value):
        # decrement first since last push will leave us one below
        self.cpu.registers["stk"] -= 1
        self.cpu.memory[self.cpu.registers["stk"]
                        ] = self.cpu.interpret_address(value)

    def _push_stk_py(self, value):
        self.cpu.registers["stk"] -= 1
        self.cpu.memory[self.cpu.registers["stk"]] = value

    @instruction()
    def call(self, function_location, *args):
        self._push_stk_py(self.cpu.registers["cur"])  # push return address to stack
        for i in args:
            self.pushstk(i)  # push vars to stack
        self.jump(function_location)

    def _pop_stk_py(self):
        if self.cpu.registers["stk"] > self.cpu.memory.size:
            return 0
        pre = self.cpu.memory[self.cpu.registers["stk"]]
        self.cpu.registers["stk"] += 1
        return pre

    @instruction()
    def ret(self, *args):
        #print("returning with args: {}".format(args))
        ret_loc = self._pop_stk_py()
        for i in args:
            self.pushstk(i)
        self.internal_jump(ret_loc)

    @instruction()
    def nop(self):
        pass
