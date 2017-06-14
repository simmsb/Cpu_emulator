# Cpu_emulator

A python version of the Little man computer

Note: I no longer work on this and am now focusing on a design that is *actually* good [here](https://github.com/nitros12/some_instruction_set)

# Description

This language is very simple. It has support for arithmetic operations, moving data around, printing integers/ characters to stdout, jumping, conditional jumps and waiting for user input.

It will automatically identify variables and assign them a place in memory (It is not smart and just groups every variable address at the start of the program, and then adds an unconditional jump at the start to cause the computer to skip the variables). It can also identify jump labels, and will assign any jumps to that location correctly. -- Dont use these

# syntax
Pretty much everything has changed to make some stuff easier.

A plain number is a plain number, use square brackets to deref to a memory location.
Derefs are parsed so you are capable of doing `[[@acc+[@stk-[@stk+4]]]]` and it will resolve.
Registers start with `@` and are accessed with their name directly (for example: `@acc`). The list of registers are:

```
CUR  < current instruction register (no reason to access directly use jump command to modify).
ACC  < accumulator, arithmetic operations are done to this register.
RAX  < general purpose register
EAX  < general purpose register
RET  < return value from functions (also general purpose)
CMP  < last comparison register. (unlike the others, this contains a string, dont touch it and you'll be fine)
STK  < Stack Pointer
LSTK < Base pointer
```


When using commands that write to a location, the command takes the memory location to write to, or the register to write to.
To write to a register, use `@reg` on it's own. to write to a location (even if you use a reg to get to that location) just do so `@reg+offset`

# Okay, Time for the command list

```
ADD <val>  <- adds Contents of register/ inline number/ contents of memory location to @ACC register.
SUB <val>  <- same as above, but subtracts.
MUL <val>  <- same as above, but multiplies, Note that because of how python does variable swapping, you can multiply the accumulator by itself.
DIV <val>
SET <val>  <- sets the accumulator to an absolute value. (as so that you dont have to reset it) (literally no reason for this to exist when you can use MOV)
MOV <@/ Memory Location (from)> <@/ Memory Location (to)>  <- moves contents of one location to the other.
CMP <@/ #/ Value> <@/ #/ Value>  <- compares the first with the second, stores in the @CMP register, if second parameter is not provided, compares with 0 instead.
JUMP <@/ #/ Value>  <- jump to location
lje, mje, leje, meje, eqje, nqje <@/ #/ Value>  <- jump to memory location if last comparison is true for [less than, more than, less than or equal, more than or equal, equal, not equal] in that order
prntint <@/ #/ Value>  <- print value to stdout
PRNTSTR <@/ #/ Value>  <- print value as a character to stdout (note does not print newline character)
PRNTNL  <- prints a newline on stdout
INPUT <@/ Memloc>  <- waits for user input on the command line and saves it into specified location
HALT  <- computer stops operation
MOVLOC <@/ Memloc (from)> <@/ Memloc (to)>  <- Moves contents of memory location at location 1 to location 2
PUSHSTK <@/ #/ Value>  <- push value to stack
POPSTK <@/ Memloc>
CALL <function> *<@/ #/ Value>  <- Call function (jump address) with arguments (syntax sugar for pushing onto stack (left to right) then jumping (handles return address for you))
RET <- Return from current function
```

Look into the directory: `example programs` for some examples.

Python stuff:

```
myprogram = Compiler(List or string of commands, Default memory size)
```

This will create a compiler object and compile the program, accessible with `myprogram.compiled`

```
mycpu = Cpu(MEMORY_SIZE, myprogram.compiled)
```

Create a CPU object with the compiled program and specified memory size (dont change memory size unless you want interesting results)

```
mycpu.execute()
```

Start executing commands from memory location 0.
