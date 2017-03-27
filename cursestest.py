from curses import newpad, newwin, wrapper


def displayStack(scrn, *stk):
    scrn.clear()

    max_width = max(map(lambda a: len(str(a)), stk))

    for c, i in enumerate(stk):
        print(f"|{c:^{max_width}}|")
        scrn.addstr(c, 0, f"{c} -> |{i:^{max_width}}|")

    scrn.refresh()


def main(stdscr):
    # Clear screen
    stdscr.clear()

    win = stdscr.derwin(20, 20, 0, 44)

    displayStack(win, 1, 4, 5, 3, 5, 3)

    stdscr.refresh()
    stdscr.getkey()

wrapper(main)
