def format_string(string, indent=0):
    string += ">"
    blocks = []
    brackets = 0
    for c, i in enumerate(string):
        if i == "<":
            brackets += 1
            blocks.append("\n{}".format("   "*brackets))
            blocks.append(i)
        elif i == ">":
            blocks.append(i)
            brackets -= 1
            if  c+1 < len(string):
                if string[c+1]  == ">":
                    blocks.append("\n{}".format("   "*brackets))
        else:
            blocks.append(i)
    return "".join(blocks)
