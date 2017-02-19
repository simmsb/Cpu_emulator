#wew compiler

+ TODO: implement asm instructions (putchar, putint, etc), jump to main at start (trivial)

##What it can do:

+ function calls: arguments can be other function calls, variables or sole numbers (no expressions)
+ return statements: return variables or sole numbers
+ math expressions: operands can be other expressions (contained within brackets), operators (number/ variables) or function calls



# syntax

+ declare functions with:
```
func funcname(params [, ...]) {
  vars {
    local:=4;
    vars:=0;
    go;
    here;
  }
  program {
    program();
    code(go, here);
    this := is + an + assignment / operation();
  }
}
```

inline asm with:
```
_asm {
  each,
  instruction,
  seperated,
  with,
  commas
}
```
