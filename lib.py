#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017  Mikaël Bouillot
#  <mikael.bouillot@bootlin.com>
#
#  Elixir is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Elixir is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Elixir.  If not, see <http://www.gnu.org/licenses/>.

import subprocess, os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def script(*args, env=None):
    args = (os.path.join(CURRENT_DIR, 'script.sh'),) + args
    # subprocess.run was introduced in Python 3.5
    # fall back to subprocess.check_output if it's not available
    if hasattr(subprocess, 'run'):
        p = subprocess.run(args, stdout=subprocess.PIPE, env=env)
        p = p.stdout
    else:
        p = subprocess.check_output(args)
    return p

# Invoke ./script.sh with the given arguments
# Returns the list of output lines

def scriptLines(*args, env=None):
    p = script(*args, env=env)
    p = p.split(b'\n')
    del p[-1]
    return p

def unescape(bstr):
    subs = (
        ('\1','\n'),
    )
    for a,b in subs:
        a = a.encode()
        b = b.encode()
        bstr = bstr.replace(a, b)
    return bstr

def decode(byte_object):
    # decode('ascii') fails on special chars
    # FIXME: major hack until we handle everything as bytestrings
    try:
        return byte_object.decode('utf-8')
    except UnicodeDecodeError:
        return byte_object.decode('iso-8859-1')

# List of tokens which we don't want to consider as identifiers
# Typically for very frequent variable names and things redefined by #define
# TODO: allow to have per project blacklists

blacklist = (
    b'NULL',
    b'__',
    b'adapter',
    b'addr',
    b'arg',
    b'attr',
    b'base',
    b'bp',
    b'buf',
    b'buffer',
    b'c',
    b'card',
    b'char',
    b'chip',
    b'cmd',
    b'codec',
    b'const',
    b'count',
    b'cpu',
    b'ctx',
    b'data',
    b'default',
    b'define',
    b'desc',
    b'dev',
    b'driver',
    b'else',
    b'end',
    b'endif',
    b'entry',
    b'err',
    b'error',
    b'event',
    b'extern',
    b'failed',
    b'flags',
    b'h',
    b'host',
    b'hw',
    b'i',
    b'id',
    b'idx',
    b'if',
    b'index',
    b'info',
    b'inline',
    b'int',
    b'irq',
    b'j',
    b'len',
    b'length',
    b'list',
    b'lock',
    b'long',
    b'mask',
    b'mode',
    b'msg',
    b'n',
    b'name',
    b'net',
    b'next',
    b'offset',
    b'ops',
    b'out',
    b'p',
    b'pdev',
    b'port',
    b'priv',
    b'ptr',
    b'q',
    b'r',
    b'rc',
    b'rdev',
    b'reg',
    b'regs',
    b'req',
    b'res',
    b'result',
    b'ret',
    b'return',
    b'retval',
    b'root',
    b's',
    b'sb',
    b'size',
    b'sizeof',
    b'sk',
    b'skb',
    b'spec',
    b'start',
    b'state',
    b'static',
    b'status',
    b'struct',
    b't',
    b'tmp',
    b'tp',
    b'type',
    b'val',
    b'value',
    b'vcpu',
    b'x'
)

# list of tokens, that are indexed as references even if no definitions are known

always_indexed_tokens = set([
# gcc/c-family/c-common.cc
    b'_Alignas',
    b'_Alignof',
    b'_Atomic',
    b'_BitInt',
    b'_Bool',
    b'_Complex',
    b'_Imaginary',
    b'_Float16',
    b'_Float32',
    b'_Float64',
    b'_Float128',
    b'_Float32x',
    b'_Float64x',
    b'_Float128x',
    b'_Decimal32',
    b'_Decimal64',
    b'_Decimal128',
    b'_Fract',
    b'_Accum',
    b'_Sat',
    b'_Static_assert',
    b'_Noreturn',
    b'_Generic',
    b'_Thread_local',
    b'__FUNCTION__',
    b'__PRETTY_FUNCTION__',
    b'__alignof',
    b'__alignof__',
    b'__asm',
    b'__asm__',
    b'__attribute',
    b'__attribute__',
    b'__auto_type',
    b'__complex',
    b'__complex__',
    b'__const',
    b'__const__',
    b'__constinit',
    b'__decltype',
    b'__extension__',
    b'__func__',
    b'__imag',
    b'__imag__',
    b'__inline',
    b'__inline__',
    b'__label__',
    b'__null',
    b'__real',
    b'__real__',
    b'__restrict',
    b'__restrict__',
    b'__signed',
    b'__signed__',
    b'__thread',
    b'__transaction_atomic',
    b'__transaction_relaxed',
    b'__transaction_cancel',
    b'__typeof',
    b'__typeof__',
    b'__typeof_unqual',
    b'__typeof_unqual__',
    b'__volatile',
    b'__volatile__',
    b'__GIMPLE',
    b'__PHI',
    b'__RTL',
    b'alignas',
    b'alignof',
    b'asm',
    b'auto',
    b'thread_local',
    b'sizeof',

# https://gcc.gnu.org/onlinedocs/gcc/_005f_005fint128.html
    b'__int128',

# https://gcc.gnu.org/onlinedocs/gcc/Floating-Types.html
    b'__float80',
    b'__ibm128',

# https://gcc.gnu.org/onlinedocs/gcc/Half-Precision.html
    b'__fp16',

# https://gcc.gnu.org/onlinedocs/gcc/Named-Address-Spaces.html
    b'__flash',
    b'__flash1',
    b'__flash2',
    b'__flash3',
    b'__flash4',
    b'__flash5',
    b'__memx',
    b'__far',
    b'__regio_symbol',
    b'__seg_fs',
    b'__seg_gs',

# https://clang.llvm.org/docs/LanguageExtensions.html#feature-checking-macros
    b'__is_identifier',

# https://clang.llvm.org/docs/LanguageExtensions.html#include-file-checking-macros
    b'__BASE_FILE__',
    b'__FILE_NAME__',
    b'__COUNTER__',
    b'__INCLUDE_LEVEL__',
    b'__TIMESTAMP__',
    b'__clang__',
    b'__clang_major__',
    b'__clang_minor__',
    b'__clang_patchlevel__',
    b'__clang_version__',
    b'__clang_literal_encoding__',
    b'__clang_wide_literal_encoding__',

# https://clang.llvm.org/docs/LanguageExtensions.html#include-file-checking-macros
    b'__datasizeof',

# https://clang.llvm.org/docs/LanguageExtensions.html#vectors-and-extended-vectors
    b'__bf16',

# https://clang.llvm.org/docs/LanguageExtensions.html#type-trait-primitives
    b'__array_rank',
    b'__array_extent',
    b'__can_pass_in_regs',
    b'__reference_binds_to_temporary',
    b'__reference_constructs_from_temporary',
    b'__reference_converts_from_temporary',
    b'__underlying_type',

# https://clang.llvm.org/docs/LanguageExtensions.html#opencl-features
    b'__remove_address_space',

# https://clang.llvm.org/docs/LanguageExtensions.html#source-location-builtins
    b'__LINE__', 
    b'__FUNCSIG__', 
    b'__FILE__',

# https://clang.llvm.org/docs/LanguageExtensions.html#arm-aarch64-language-extensions
    b'__dmb',
    b'__dsb',
    b'__isb',

# https://en.cppreference.com/w/c/language/attributes
    b'deprecated',
    b'fallthrough',
    b'maybe_unused',
    b'nodiscard',
    b'noreturn',
    b'_Noreturn',
    b'unsequenced',
    b'reproducible'

# https://en.cppreference.com/w/cpp/language/attributes
    b'noreturn',
    b'carries_dependency',
    b'likely',
    b'unlikely',
    b'no_unique_address',
    b'assume',
    b'indeterminate',
    b'optimize_for_synchronized',
])

always_indexed_prefixes = (
    b'__builtin',

# https://gcc.gnu.org/onlinedocs/gcc/_005f_005fsync-Builtins.html
    b'__sync',

# https://gcc.gnu.org/onlinedocs/gcc/_005f_005fatomic-Builtins.html
    b'__atomic',
    b'__ATOMIC',

# https://clang.llvm.org/docs/LanguageExtensions.html#feature-checking-macros
# https://clang.llvm.org/docs/LanguageExtensions.html#include-file-checking-macros
    b'__has',

# https://clang.llvm.org/docs/LanguageExtensions.html#language-extensions-back-ported-to-previous-standards
    b'__cpp',

# https://clang.llvm.org/docs/LanguageExtensions.html#type-trait-primitives
    b'__is',

# https://clang.llvm.org/docs/LanguageExtensions.html#opencl-features
    b'__cl',
)

def isIdent(bstr):
    if (len(bstr) < 2 or
        bstr in blacklist or
        bstr.startswith(b'~')):
        return False
    else:
        return True

def autoBytes(arg):
    if type(arg) is str:
        arg = arg.encode()
    elif type(arg) is int:
        arg = str(arg).encode()
    return arg

def getDataDir():
    try:
        dir=os.environ['LXR_DATA_DIR']
    except KeyError:
        print(argv[0] + ': LXR_DATA_DIR needs to be set')
        exit(1)
    return dir

def getRepoDir():
    try:
        dir=os.environ['LXR_REPO_DIR']
    except KeyError:
        print(argv[0] + ': LXR_REPO_DIR needs to be set')
        exit(1)
    return dir

def currentProject():
    return os.path.basename(os.path.dirname(getDataDir()))

# List all families supported by Elixir
families = ['A', 'B', 'C', 'D', 'K', 'M']

def validFamily(family):
    return family in families

def getFileFamily(filename):
    name, ext = os.path.splitext(filename)

    if ext.lower() in ['.c', '.cc', '.cpp', '.c++', '.cxx', '.h', '.s'] :
        return 'C' # C file family and ASM
    elif ext.lower() in ['.dts', '.dtsi'] :
        return 'D' # Devicetree files
    elif name.lower()[:7] in ['kconfig'] and not ext.lower() in ['.rst']:
        # Some files are named like Kconfig-nommu so we only check the first 7 letters
        # We also exclude documentation files that can be named kconfig
        return 'K' # Kconfig files
    elif name.lower()[:8] in ['makefile'] and not ext.lower() in ['.rst']:
        return 'M' # Makefiles
    else :
        return None

# 1 char values are file families
# 2 chars values with a M are macros families
compatibility_list = {
    'C' : ['C', 'K'],
    'K' : ['K'],
    'D' : ['D', 'CM'],
    'M' : ['K']
}

# Check if families are compatible
# First argument can be a list of different families
# Second argument is the key for choosing the right array in the compatibility list
def compatibleFamily(file_family, requested_family):
    return any(item in file_family for item in compatibility_list[requested_family])

# Check if a macro is compatible with the requested family
# First argument can be a list of different families
# Second argument is the key for choosing the right array in the compatibility list
def compatibleMacro(macro_family, requested_family):
    result = False
    for item in macro_family:
        item += 'M'
        result = result or item in compatibility_list[requested_family]
    return result
