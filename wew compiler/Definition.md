Program begins with `PROGRAM <name>` and ends with `ENDPROGRAM`
Functions begin with `FUNCTION *<params>` and end with `ENDFUNCTION`
There has to exist a `main` function that accepts no input and returns nothing

no embedded functions inside functions

all variables declared at start of functions

example:

```
FUNCTION main
VARS
wew
lad
ayy
BEGIN

wew = INPUT
lad = INPUT

ayy = addTWo(wew, lad)

print ayy

ENDFUNCTION


FUNCTION addTwo a b
BEGIN

RETURN a + b

ENDFUNCTION
```
