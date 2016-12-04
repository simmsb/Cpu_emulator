import re


"""
Idea of this:

every line gets placed into a BaseSyntax object.

then each syntax object is iterated over until there are no non parsed code left.

then from the roots the syntax is compiled into the assembly

before finally being placed
"""

class BaseSyntax:
    """Base syntax object for holding syntax"""


    syntax_recognise = re.compile(".+(?=;)")


    def __init__(self, parent=None, syntax_block):
        self.parent = parent
        self.syntax_block = syntax_block
        if self.parent:
            parent.initialize_child(self)
