#!/usr/bin/python3

import subprocess
import re
import sys

def echo (bstr):
    sys.stdout.buffer.write (bstr)

def script (*args):
    args = ('./script.sh',) + args
    p = subprocess.run (args, stdout=subprocess.PIPE)
    p = p.stdout
    return p

def scriptLines (*args):
    p = script (*args)
    p = p.split (b'\n')
    del p[-1]
    return p

def unescape (bstr):
    subs = (
        ('<','\033[32m/*'),
        ('>','*/\033[0m'),
        ('\1','\n'),
        ('\2','<'),
        ('\3','>'))
    for a,b in subs:
        a = a.encode()
        b = b.encode()
        bstr = bstr.replace (a, b)
    return bstr

blacklist = (
    b'struct',
    b'static',
    b'define',
    b'NULL',
    b'sizeof',
    b'status',
    b'device',
    b'adapter',
    b'inline',
    b'offset',
    b'failed',
    b'dentry',
    b'retval',
    b'buffer',
    b'length',
    b'result',
    b'unlikely',
    b'extern',
    b'driver',
    )

def isIdent (bstr):
    if len (bstr) < 3:
        return False
    elif bstr in blacklist:
        return False
    elif re.search (b'_', bstr):
        return True
    elif re.search (b'^[A-Z0-9]*$', bstr):
        return True
    elif len (bstr) >= 6:
        return True
    else:
        return False

def autoBytes (arg):
    if type (arg) is str:
        arg = arg.encode()
    elif type (arg) is int:
        arg = str(arg).encode()
    return arg
