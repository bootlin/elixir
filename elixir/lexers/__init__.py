from .lexers import *

default_lexers = {
    r'.*\.(c|h|cpp|hpp|c++|cxx|cc)': CLexer,
    r'makefile\..*':  MakefileLexer,
    r'.*\.dts(i)?': DTSLexer,
    r'.*\.s': GasLexer,
    r'kconfig.*': KconfigLexer, #TODO negative lookahead for .rst
}

