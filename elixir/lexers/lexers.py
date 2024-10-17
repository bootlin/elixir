import re

from . import shared
from .utils import TokenType, simple_lexer, FirstInLine

# Lexers used to extract possible references from source files
# Design inspired by Pygments lexers interface

# https://en.cppreference.com/w/c/language
# https://www.iso-9899.info/wiki/The_Standard
class CLexer:
    # NOTE: does not support unicode identifiers
    c_identifier = r'[a-zA-Z_][a-zA-Z_0-9]*'

    c_punctuation = r'[!#%&`()*+,./:;<=>?\[\]\\^_{|}~-]'

    # NOTE: macros don't always contain C code, but detecting that in pratice is hard
    # without information about context (where the file is included from).
    c_punctuation_extra = r'[$\\@]'

    rules = [
        (shared.whitespace, TokenType.WHITESPACE),
        (shared.common_slash_comment, TokenType.COMMENT),
        (shared.common_string_and_char, TokenType.STRING),
        (shared.c_number, TokenType.NUMBER),
        (c_identifier, TokenType.IDENTIFIER),
        (FirstInLine(shared.c_preproc_ignore), TokenType.SPECIAL),
        (c_punctuation, TokenType.PUNCTUATION),
        (c_punctuation_extra, TokenType.PUNCTUATION),
    ]

    def __init__(self, code):
        self.code = code

    def lex(self, **kwargs):
        return simple_lexer(self.rules, self.code, **kwargs)


