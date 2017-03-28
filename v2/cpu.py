import interrupts
import memory
import instructions


class registers:

    def __init__(self):
        self.esp = 0
        self.rax = 0
        self.eax = 0
        self.brt = 0
        self.cur = 0
        self.cmp = 0
        self.stk = 0
        sel.lstk = 0

class cpu:

    def __init__(self, msize, iset=instructions.iset):
        self.memory = memory.memory(msize)
        self.iset = iset
        self.interrupts = interrupts.interrupts
        self.registers = registers()

        self.stk = msize

    def load_program(self, program):
        self.memory.load(program)

    def deploy_interrupt(self, *, itype, defer):
        self.interrupts.deploy(self, itype=itype, defer=defer)

    def exec_command(self, code):
        self.iset.run(code, self)

    def push(self, val):


    def run(self):
        while True:
            try:
                mem = self.memory[self.registers.cur]
                self.registers.cur += 1
                self.exec_command(mem)
                itype = self.interrupts.check()
                if itype is not None:

