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

import subprocess

def script (*args):
    args = ('./script.sh',) + args
    # subprocess.run was introduced in Python 3.5
    # fall back to subprocess.check_output if it's not available
    if hasattr(subprocess, 'run'):
        p = subprocess.run (args, stdout=subprocess.PIPE)
        p = p.stdout
    else:
        p = subprocess.check_output(args)
    return p

def scriptLines (*args):
    p = script (*args)
    p = p.split (b'\n')
    del p[-1]
    return p

def unescape (bstr):
    subs = (
        ('\1','\n'),
    )
    for a,b in subs:
        a = a.encode()
        b = b.encode()
        bstr = bstr.replace (a, b)
    return bstr

blacklist = (
    b'if',
    b'dev',
    b'i',
    b'ret',
    b'err',
    b'flags',
    b'h',
    b'data',
    b'const',
    b'skb',
    b'len',
    b'name',
    b'priv',
    b'p',
    b'val',
    b'info',
    b'buf',
    b'rc',
    b'type',
    b'out',
    b'cmd',
    b'port',
    b'size',
    b'page',
    b'tp',
    b'pdev',
    b'state',
    b'addr',
    b'rdev',
    b'sk',
    b'count',
    b'hw',
    b'lock',
    b'error',
    b'reg',
    b's',
    b'id',
    b'tmp',
    b'codec',
    b'req',
    b'bp',
    b'c',
    b'chip',
    b'r',
    b'n',
    b'value',
    b'start',
    b'index',
    b'res',
    b'regs',
    b'j',
    b'base',
    b'irq',
    b'x',
    b'net',
    b'mode',
    b'vcpu',
    b'host',
    b'spec',
    b'card',
    b'sb',
    b'mask',
    b'list',
    b'ops',
    b'next',
    b'ctx',
    b'event',
    b'mddev',
    b'q',
    b'attr',
    b'cpu',
    b'desc',
    b'msg',
    b't',
    b'entry',
    b'arg',
    b'idx',
    b'end',
    b'root',
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
    b'extern',
    b'driver',
    )

def isIdent (bstr):
    if len (bstr) < 2:
        return False
    elif bstr in blacklist:
        return False
    else:
        return True

def autoBytes (arg):
    if type (arg) is str:
        arg = arg.encode()
    elif type (arg) is int:
        arg = str(arg).encode()
    return arg
