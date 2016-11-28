class MemoryOverFlowException(Exception):
    pass


class Memory:
    """Holds memory cells for computer

    Arguments
    ---------

    memory_size: <int> number of memory cells to allocate

    default: <int> default value for all non initialised memory cells to begin with

    Functions
    ---------

    load_program( Program ): Load program into memory, note does not reset non written to cells
    """

    def __init__(self, memory_size, default=0):
        self.default = default if isinstance(default, int) else 0
        self.cells = [default] * memory_size

    def load_program(self, program):
        """Loads program into memory

        Arguments
        ---------

        program: <iterator> compiled program to insert into main memory"""
        for i, j in enumerate(program):
            self.cells[i] = j

    def __getitem__(self, key):
        if len(self.cells) < int(key):
            raise MemoryOverFlowException("SEGFAULT: Attempt to access memory",
                                          " location outside of physical capacity (Address: {})".format(key))
        else:
            return self.cells[key]

    def __setitem__(self, key, value):
        if len(self.cells) < int(key):
            raise MemoryOverFlowException("SEGFAULT: Attempt to set memory",
                                          " location outside of physical capacity (Address: {})".format(key))
        else:
            self.cells[key] = value

    def __delitem__(self, key):
        if len(self.cells) < int(key):
            raise MemoryOverFlowException("SEGFAULT: Attempt to set memory",
                                          " location outside of physical capacity (Address: {})".format(key))
        else:
            self.cells[key] = 0

    @property
    def size(self):
        return len(self.cells)
