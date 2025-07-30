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

import sys
import logging
import subprocess, os

logger = logging.getLogger(__name__)

CURRENT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../')

def script(*args, input=None, env=None):
    args = (os.path.join(CURRENT_DIR, 'script.sh'),) + args
    # subprocess.run was introduced in Python 3.5
    # fall back to subprocess.check_output if it's not available
    if hasattr(subprocess, 'run'):
        p = subprocess.run(args, stdout=subprocess.PIPE, input=input, env=env)
        p = p.stdout
    else:
        p = subprocess.check_output(args, input=input)
    return p

def run_cmd(*args, env=None):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if len(p.stderr) != 0:
        logger.error('command %s printed to stderr: \n%s', str(args), p.stderr.decode('utf-8'))
    return p.stdout, p.returncode

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
        return os.environ['LXR_DATA_DIR']
    except KeyError:
        print(sys.argv[0] + ': LXR_DATA_DIR needs to be set')
        exit(1)

def getRepoDir():
    try:
        return os.environ['LXR_REPO_DIR']
    except KeyError:
        print(sys.argv[0] + ': LXR_REPO_DIR needs to be set')
        exit(1)

def currentProject():
    return os.path.basename(os.path.dirname(getDataDir()))

# List all families supported by Elixir
families = ['A', 'B', 'C', 'D', 'K', 'M']

# Those families have databases that cache the content of definitions.db.
# This allows faster lookup.
CACHED_DEFINITIONS_FAMILIES = ['C', 'K', 'D', 'M']

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
