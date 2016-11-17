from components import *
import glob
import os

MEMORY_SIZE = 500

files = glob.glob(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "example_programs", "*.txt"))

filedict = {}

for i, c in enumerate(files):
    print("{}: {}".format(i, c.split(os.pathsep)[-1]))
    filedict[str(i)] = c  # generate dict here for ease of entering input

while True:
    program = filedict.get(input("Index of program to run: "))
    if program: break


with open(program) as commandList:
    commands = [i.strip("\n") for i in list(commandList)]


myprogram = Compiler(commands, MEMORY_SIZE)
myprogram.compile()

mycpu = Cpu(MEMORY_SIZE, myprogram.compiled)


mycpu.execute()
