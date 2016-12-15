from components import cpu
from ReversePolish import parser

MEMORY_SIZE = 500

commands = '35*5-'

polish_script = parser.Parser(commands)
print('Source: {}, compiled: {}'.format(polish_script.source, polish_script.compiled))
polish_program = cpu.Compiler(polish_script.compiled, MEMORY_SIZE)
compiled = list(polish_program.compiled)
print('Source: {}, compiled: {}\n'.format(None, compiled))
polish_cpu = cpu.Cpu(memory_capacity=MEMORY_SIZE, program=compiled)
polish_cpu.execute()
