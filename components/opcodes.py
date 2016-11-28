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


def exception_wrapper(func):
    def decorator(*args):
        try:
            print("executing function")
            return func(*args)
        except TypeError:
            raise Exception("Instruction received invalid amount of arguments",
                            "expected {}, recieved {}".format(func.__code__.co_argcount, len(args)))
        except ValueError:  # we assume a value error is caused by attempting to treat an absolute value as a mutable object
            raise Exception("Attempt to use absolute value (#) as mutable type")
    decorator.__name__ = func.__name__
    decorator.__doc__ = func.__doc__
    return decorator


class InstructionSet:
    """Container for cpu instructions

    Arguments
    ---------

    cpu: <cpu object> CPU object to use to execute commands
        Not needed if only being used to compile a program


    Functions
    ---------

    run_encoded( command, *args ): Execute a decoded instruction

    encode_name( command_name ): Return numeric ID of a instruction, returns None if non existant instruction
    """

    def __init__(self, cpu=None):  # no cpu needed for compiler
        self.encoded_commands = instruction_map.copy()
        self.instruction_names = instruction_names.copy()
        self.cpu = cpu

    def run_encoded(self, command, *args):
        """Run an encoded instruction

        Arguments
        ---------

        command: <int> Decoded command to execute

        *args: <str> Operands to run instruction with"""
        command = self.encoded_commands.get(command)
        if command:
            command(self, *args)
        else:
            raise CpuStoppedCall(
                "Invalid command, ID was: {}. Arguments were: {}".format(command, args))

    def encode_name(self, command_name):
        return self.instruction_names.get(command_name)


    @instruction()
    @exception_wrapper
    def add(self, value):
        self.cpu.registers["acc"] += self.cpu.interpret_address(value)


    @instruction()
    @exception_wrapper
    def sub(self, value):
        self.cpu.registers["acc"] -= self.cpu.interpret_address(value)


    @instruction()
    @exception_wrapper
    def mul(self, value):
        self.cpu.registers["acc"] *= self.cpu.interpret_address(value)


    @instruction()
    @exception_wrapper
    def div(self, value):
        self.cpu.registers["acc"] /= self.cpu.interpret_address(value)


    @instruction()
    @exception_wrapper
    def set(self, value):
        self.cpu.registers["acc"] = self.cpu.interpret_address(value)


    @instruction()
    @exception_wrapper
    def mov(self, from_loc, to_loc):
        if to_loc.startswith("@"):
            self.cpu.registers[to_loc.lstrip(
                "@")] = self.cpu.interpret_address(from_loc)
        else:
            self.cpu.memory[int(to_loc)] = self.cpu.interpret_address(from_loc)


    @instruction()
    @exception_wrapper
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

    def _internal_jump(self, location):  # jumps to memory address provided, no interpreting
        self.cpu.registers["cur"] = location


    @instruction()
    @exception_wrapper
    def jump(self, jump):
        self._internal_jump(self.cpu.interpret_address(jump))


    @instruction()
    @exception_wrapper
    def _test_cmp(self, index):
        return int(self.cpu.registers["cmp"][index])


    @instruction()
    @exception_wrapper
    def lje(self, jump):  # less than
        if self._test_cmp(0):
            self.jump(jump)


    @instruction()
    @exception_wrapper
    def mje(self, jump):  # more than
        if self._test_cmp(1):
            self.jump(jump)


    @instruction()
    @exception_wrapper
    def leje(self, jump):  # less than equal
        if self._test_cmp(2):
            self.jump(jump)


    @instruction()
    @exception_wrapper
    def meje(self, jump):  # more than equal
        if self._test_cmp(3):
            self.jump(jump)


    @instruction()
    @exception_wrapper
    def eqje(self, jump):  # equal
        if self._test_cmp(4):
            self.jump(jump)


    @instruction()
    @exception_wrapper
    def prntint(self, memloc):
        print(self.cpu.interpret_address(memloc))


    @instruction()
    @exception_wrapper
    def prntstr(self, memloc):
        print(chr(self.cpu.interpret_address(memloc)), end='')


    @instruction()
    @exception_wrapper
    def prntnl(self):
        print("\n")


    @instruction()
    @exception_wrapper
    def input(self, memloc):
        if memloc.startswith("@"):
            self.cpu.registers[memloc.strip("@").lower()] = int(
                input("Enter number: "))
        else:
            self.cpu.memory[int(memloc)] = int(input("Enter number: "))

      # like anything wrong could happen here
    @instruction()
    @exception_wrapper
    def halt(self):
        raise CpuStoppedCall("CPU halt triggered")


    @instruction()
    @exception_wrapper
    def movloc(self, from_loc, to_loc):
        # move from location stored in location to location
        if to_loc.startswith("@"):
            self.cpu.registers[to_loc.lstrip("@")] = self.cpu.memory[
                self.cpu.interpret_address(from_loc)]
        else:
            self.cpu.memory[int(to_loc)] = self.cpu.memory[
                self.cpu.interpret_address(from_loc)]


    @instruction()
    @exception_wrapper
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
    @exception_wrapper
    def pushstk(self, value):
        # decrement first since last push will leave us one below
        self.cpu.registers["stk"] -= 1
        self.cpu.memory[self.cpu.registers["stk"]
                        ] = self.cpu.interpret_address(value)

    def _push_stk_py(self, value):
        self.cpu.registers["stk"] -= 1
        self.cpu.memory[self.cpu.registers["stk"]] = value


    @instruction()
    @exception_wrapper
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
    @exception_wrapper
    def ret(self, *args):
        #print("returning with args: {}".format(args))
        ret_loc = self._pop_stk_py()
        for i in args:
            self.pushstk(i)
        self._internal_jump(ret_loc)


    @instruction()
    @exception_wrapper
    def nop(self):
        pass
