class MemoryOverFlowException(Exception):
    pass

class Memory:
    def __init__(self, size, default):
        self.cells = [default for i in range(size)]

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


class InstructionSet:
    def add(self, memory_loc, value):
        self.memory[int(memory_loc)] += self.interpret_address(value)

    def sub(self, memory_loc, value):
        self.memory[int(memory_loc)] -= self.interpret_address(value)

    def mul(self, memory_loc, value):
        self.memory[int(memory_loc)] *= self.interpret_address(value)

    def sub(self, memory_loc, value):
        self.memory[int(memory_loc)] /= self.interpret_address(value)

    def set(self, memory_loc, value):
        self.memory[int(memory_loc)] = self.interpret_address(value)

    def mov(self, from_loc, to_loc):
        self.memory[self.interpret_address(to_loc)] = self.memory[self.interpret_address(from_loc)]

class Registers:
    def __init__(self):
        self.CUR = 0
        self.ACC = 0
        self.RAX = 0
        self.EAX = 0
        self.RET = 0


class Cpu(InstructionSet, Registers):
    def __init__(self, memory_capacity):
        self.memory = Memory(memory_capacity, 0)
        Registers.__init__(self)

    def decode_command(self, string):
        codes = string.split()
        opcode = codes.pop(0)
        self.execute_command(opcode, *codes)

    def execute_command(self, opcode, *codes):
        command = self.__getattribute__(opcode)
        command(*codes)

    def interpret_address(self, string):
        '''#3 for immediate
        3 for memory_location'''
        return int(string.lstrip("#")) if string.startswith("#") else self.memory[int(string)]


class Compiler:
    def __init__(self, memory_size):
        pass
    # Todo: add ability to compile program into a list of functors

mycpu = Cpu(400)
# Todo: add interpretation of assembly file
