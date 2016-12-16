Follows C like syntax, but modified a bit

example:

```
func main()
{
    vars
    {
        a := 5;
        b;
        c;
    }
    program
    {
        b := a*4;
        c := addtwo(b, 1);
        print(c)
        return() ; return is a function
    }
}


func addtwo(a, b)
{
    program
    {
        return(a + b);
    }
}
```

would become:

```
call main  ; program entry point
halt

_main nop
pushstk #5
pushstk #0
pushstk #0
mov [@stk+2] @acc
mul #4
mov @acc [@stk+1]
call addtwo [@stk+1] #1
mov @ret [@stk+0]
prntint [@stk+0]
popstk
popstk
popstk
ret

_addtwo nop
mov [@stk+0] @acc
add [@stk+1]
mov @acc @ret
popstk
popstk
ret
```