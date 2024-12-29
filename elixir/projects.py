from collections import OrderedDict
from .filters import *
from .lexers import *

# Dictionary of custom per-projects settings.
# filters:
# Projects not present in this dictionary only use default_filters.
# Use `*` to unpack filter lists defined above,
# you can pass additional options to filters by putting a Filter
# class and a dictionary with options in a tuple, like this:
# (FilterCls, {"option": True}).
# Check filter files and utils.py for information about available options
projects = {
    'amazon-freertos': {
        'filters': [
            *default_filters,
            MakefileSubdirFilter,
        ],
    },
    'arm-trusted-firmware': {
        'filters': [
            *default_filters,
            CppPathIncFilter,
        ],
    },
    'barebox': {
        'filters': [
            *default_filters,
            DtsiFilter,
            *common_kconfig_filters,
            CppPathIncFilter,
            *common_makefile_filters,
        ],
    },
    'coreboot': {
        'filters': [
            *default_filters,
            DtsiFilter,
            *common_kconfig_filters,
            *common_makefile_filters,
        ],
    },
    'linux': {
        'filters': [
            *default_filters,
            DtsiFilter,
            *common_kconfig_filters,
            *common_makefile_filters,
            # include/uapi contains includes to user headers under #ifndef __KERNEL__
            # Our solution is to ignore all includes in such paths
            (CppPathIncFilter, {"path_exceptions": {'^/include/uapi/.*'}}),
        ],
        'lexers': OrderedDict({
            r'.*\.(c|h|cpp|hpp|c++|cxx|cc)': CLexer,
            r'makefile\..*':  MakefileLexer,
            r'.*\.dts(i)?': DTSLexer,
            r'kconfig.*': KconfigLexer, #TODO negative lookahead for .rst

            r'/arch/alpha/.*\.s': (GasLexer, {"arch": "alpha"}),
            r'/arch/arc/.*\.s': (GasLexer, {"arch": "arc"}),
            r'/arch/arm/.*\.s': (GasLexer, {"arch": "arm32"}),
            r'/arch/csky/.*\.s': (GasLexer, {"arch": "csky"}),
            r'/arch/m68k/.*\.s': (GasLexer, {"arch": "m68k"}),
            r'/arch/microblaze/.*\.s': (GasLexer, {"arch": "microblaze"}),
            r'/arch/mips/.*\.s': (GasLexer, {"arch": "mips"}),
            r'/arch/openrisc/.*\.s': (GasLexer, {"arch": "openrisc"}),
            r'/arch/parisc/.*\.s': (GasLexer, {"arch": "parisc"}),
            r'/arch/s390/.*\.s': (GasLexer, {"arch": "s390"}),
            r'/arch/sh/.*\.s': (GasLexer, {"arch": "sh"}),
            r'/arch/sparc/.*\.s': (GasLexer, {"arch": "sparc"}),
            r'/arch/um/.*\.s': (GasLexer, {"arch": "x86"}),
            r'/arch/x86/.*\.s': (GasLexer, {"arch": "x86"}),
            r'/arch/xtensa/.*\.s': (GasLexer, {"arch": "xtensa"}),
            r'.*\.s': GasLexer,
        }),
    },
    'qemu': {
        'filters': [
            *default_filters,
            *common_kconfig_filters,
        ],
    },
    'u-boot': {
        'filters': [
            *default_filters,
            DtsiFilter,
            *common_kconfig_filters,
            CppPathIncFilter,
            *common_makefile_filters,
        ],
        'lexers': OrderedDict({
            r'.*\.(c|h|cpp|hpp|c++|cxx|cc)': CLexer,
            r'makefile\..*':  MakefileLexer,
            r'.*\.dts(i)?': DTSLexer,
            r'kconfig.*': KconfigLexer, #TODO negative lookahead for .rst

            r'/arch/arc/.*\.s': (GasLexer, {"arch": "arc"}),
            r'/arch/arm/.*\.s': (GasLexer, {"arch": "arm32"}),
            r'/arch/m68k/.*\.s': (GasLexer, {"arch": "m68k"}),
            r'/arch/microblaze/.*\.s': (GasLexer, {"arch": "microblaze"}),
            r'/arch/mips/.*\.s': (GasLexer, {"arch": "mips"}),
            r'/arch/riscv/.*\.s': (GasLexer, {"arch": "riscv"}),
            r'/arch/sh/.*\.s': (GasLexer, {"arch": "sh"}),
            r'/arch/x86/.*\.s': (GasLexer, {"arch": "x86"}),
            r'/arch/sandbox/.*\.s': (GasLexer, {"arch": "x86"}),
            r'/arch/xtensa/.*\.s': (GasLexer, {"arch": "xtensa"}),
            r'.*\.s': GasLexer,
        }),
    },
    'uclibc-ng': {
        'filters': [
            *default_filters,
            ConfigInFilter,
        ],
    },
    'zephyr': {
        'filters': [
            *default_filters,
            DtsiFilter,
            *common_kconfig_filters,
            CppPathIncFilter,
        ],
    },
}

