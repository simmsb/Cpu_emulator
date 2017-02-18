from compiler import *
from formatter import format_string
a = OperationsObjects()

print(a.parse("wew();"))
print(a.parse("wew(lad, ayy, lmao);"))
print(a.parse("wew(lad);"))
print(a.parse("wew(lad(ayy), ayy);"))
print(a.parse("wew(lad(ayy(lmao(test))));"))
print(a.parse("wew(lad(ayy()));"))

print(a.parse("A := A + B - C;"))
print(a.parse("A := func() + c * 5;"))

print(
    a.parse("while(a>b){wew();lad(wew());if(a<b){dothis();}}}"))

b = FunctionDefineParser()
c = ProgramSolver()
print(format_string(
    str(c.parse("""func wew(a,b,c){
                        vars {
                            a := 2;
                            b := 4;
                        }
                        program {
                            if(this<that){
                            call();
                            }
                        }
                    }""")[0])))

program1 = """
func addtwo(a, b) {
    program {
        a := a + b;
        return a;
    }
}

func comparenums(this, that){
    vars {
        a := 2;
    }
    program {
        a := addtwo(a, a);
        this := a * this;
        if (this<that) {
            return that;
        }
        return this;
    }
}
"""
min_ = program1.strip("\n")
for i in min_:
    print(min_)

parsed = c.parse(min_)
for i in parsed:
    i.parent_own_children()
    print(format_string(str(i)))

for i in parsed:
    print("\n".join(i.assemble()))
