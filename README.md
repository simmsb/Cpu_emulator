# Cpu_emulator
A python version of the Little man computer


#Description
This language is very simple. It has support for arithmetic operations, moving data around, printing integers/ characters to stdout, jumping, conditional jumps and waiting for user input.

It will automatically identify variables and assign them a place in memory (It is not smart and just groups every variable address at the start of the program, and then adds an unconditional jump at the start to cause the computer to skip the variables). It can also identify jump labels, and will assign any jumps to that location correctly.

#syntax
In place integers start with ```#``` and are followed by the number, ie: ```#5```.

Memory addresses are accessed with a plain integer, like ```5``` (this points to memory address 5). Note that you should index memory addresses starting from 1, as there is always a unconditional jump to the start (and also remember that all variables are moved to the start of the program). You could also just use a variable instead, like ```varFive``` and just reuse it as needed.

Registers start with ```@``` and are accessed with their name directly.
The list of registers are:

```
CUR  < current instruction register (no reason to access directly use jump command to modify).
ACC  < accumulator, arithmetic operations are done to this register.
RAX  < general purpose register (ideally store function returns here)
EAX  < general purpose register
RET  < function jump return
CMP  < last comparison register. (unlike the others, this contains a string, dont touch it and you'll be fine)
STK  < current stack position (leave it for popstk and pushstk to handle)
```

Variables are assigned as any non-command word followed by a initial value (if none provided, it is set to 0)
for example ```myVariable 5```, this can be accessed again at any time with ```myVariable```. Note that the way the program is compiled, all instances of the varible name are replaced with it's assigned memory location, so you can't do ```#myVariable``` to get to a memory location contained in a memory location, instead you should use the command ```fromloc <from> <to>``` which will retrieve the contents of the memory location stored at a loction.
Note that all variables are removed from the command list and placed at the end of the program,
because of this you should not mix use of absolute location memory references and labels, as the index of a location could change depending on whether it was in front of or behind a label.
Also, variables have no scope, they are always global, use the stack if you want to have semi scoped function variables


Jump labels are assigned as any word starting with the character ```_```, and should be referenced with the name without the ```_```
an example of a jump label would be: ```_myJump```. Jump definitions should always precede a command (for example: ```_myJump mov @acc myVar```
You would then jump to that location with ```jump myVar```
You should always use jump labels instead of absolute references, as the index of a command/ function can change depending on where you defined variables

Comments start with ```;```, there are no multi line comments, only lines starting with ```;``` only. whitespace between the last operand and the comment is sorted for you.

In place addition/ subtraction is done with ```[arg1+arg2]```. Currently labels are not supported because of how the preprocessor handles the conversion to memory addresses (I'll fix this soon)

Because of this stack scope can be used (Ideally you should use the stack entirely now, eliminating the need for globals)

#Okay, Time for the command list

```
ADD <@/ #/ Value>  <- adds Contents of register/ inline number/ contents of memory location to @ACC register.
SUB <@/ #/ Value>  <- same as above, but subtracts.
MUL <@/ #/ Value>  <- same as above, but multiplies, Note that because of how python does variable swapping, you can multiply the accumulator by itself.
DIV <@/ #/ Value>
SET <@/ #/ Value>  <- sets the accumulator to an absolute value. (as so that you dont have to reset it) (literally no reason for this to exist when you can use MOV)
MOV <@/ Memory Location (from)> <@/ Memory Location (to)>  <- moves contents of one location to the other.
CMP <@/ #/ Value> <@/ #/ Value>  <- compares the first with the second, stores in the @CMP register, if second parameter is not provided, compares with 0 instead.
JUMP <@/ #/ Value>  <- jump to location
lje, mje, leje, meje, eqje <@/ #/ Value>  <- jump to memory location if last comparison is true for [less than, more than, less than or equal, more than or equal, equal] in that order
prntint <@/ #/ Value>  <- print value to stdout
PRNTSTR <@/ #/ Value>  <- print value as a character to stdout (note does not print newline character)
PRNTNL  <- prints a newline on stdout
INPUT <@/ Memloc>  <- waits for user input on the command line and saves it into specified location
HALT  <- computer stops operation
MOVLOC <@/ Memloc (from)> <@/ Memloc (to)>  <- Moves contents of memory location at location 1 to location 2
PUSHSTK <@/ #/ Value>  <- push value to stack
POPSTK <@/ Memloc>
CALL <function> *<@/ #/ Value>  <- Call function (jump address) with arguments (syntax sugar for pushing onto stack (left to right) then jumping (handles return address for you))
RET *<@/ #/ Values>  <- Return from current function with arguments (arguments are loaded left to right)
```

Look into the directory: ```example programs``` for some examples.


Python stuff:

```
myprogram = Compiler(List or string of commands, Default memory size)
```
This will create a compiler object and compile the program, accessible with ```myprogram.compiled```


```
mycpu = Cpu(MEMORY_SIZE, myprogram.compiled)
```
Create a CPU object with the compiled program and specified memory size (dont change memory size unless you want interesting results)

```
mycpu.execute()
```
Start executing commands from memory location 0.
