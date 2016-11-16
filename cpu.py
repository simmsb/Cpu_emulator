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
    def add(self, value, *_):
        self.registers["acc"] += self.interpret_address(value)

    def sub(self, value):
        self.registers["acc"] += self.interpret_address(value)
        
    def mul(self, value):
        self.registers["acc"] += self.interpret_address(value)

    def sub(self, value):
        self.registers["acc"] += self.interpret_address(value)

    def set(self, value):
        self.registers["acc"] += self.interpret_address(value)

    def mov(self, from_loc, to_loc):
        # move from register to location
        if to_loc.startswith("@"):
            self.registers[to_loc.lstrip("@")] = self.interpret_address(from_loc)
        else:
            self.memory[int(to_loc)] = self.interpret_address(from_loc)
        

class Registers:
    def __init__(self):
        self.register_memory = [0 for i in range(5)]
        self.register_map = {
            "cur":0,
            "acc":1,
            "rax":2,
            "eax":3,
            "ret":4
            }

    def __getitem__(self, key):
        return self.register_memory[self.register_map[key]]

    def __setitem__(self, key, value):
        self.register_memory[self.register_map[key]] = value


class Cpu(InstructionSet):
    def __init__(self, memory_capacity):
        self.memory = Memory(memory_capacity, 0)
        self.registers = Registers()

    def decode_command(self, string):
        codes = string.lower().split()
        opcode = codes.pop(0)
        self.execute_command(opcode, *codes)

    def execute_command(self, opcode, *codes):
        command = self.__getattribute__(opcode)
        command(*codes)


    def interpret_address(self, string):
        '''#3 for immediate
        @reg for register
        3 for memory_location'''
        def interpret_memory_location(string):
            return self.registers.__getattribute__(string.lstrip("@")) if string.startswith("@") else self.memory[int(string)]
        
        return int(string.lstrip("#")) if string.startswith("#") else interpret_memory_location(string)


class Compiler:
    def __init__(self, memory_size):
        pass
    # Todo: add ability to compile program into a list of functors

mycpu = Cpu(400)
# Todo: add interpretation of assembly file
