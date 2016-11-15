class cpu_commands(object):
    def add(self, memory_loc, value):
        self.memory[int(memory_loc)] += self.interpret_address(value)

class cpu(cpu_commands):
    def __init__(self, initial_size):
        self.memory = [0 for i in range(initial_size)]
        self.commands = cpu_commands

    def run_command(self, string):
        codes = string.split()
        opcode = codes.pop(0)
        self.execute_command(opcode, *codes)

    def execute_command(self, opcode, *codes):
        command = self.commands.get_command(opcode)
        command(self, *codes)

    def interpret_address(self, string):
        '''#3 for immediate
        3 for memory_location'''
        return int(string.lstrip("#")) if string.startswith("#") else self.memory[int(string)]


class Compiler(object):
    def __init__(self, memory_size):
        pass

mycpu = cpu(400)