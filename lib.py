#!/usr/bin/python3

import subprocess
import bsddb3
import re

def echo (bstr):
    print (bstr.decode(), end='')

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
        ('<','/*'),
        ('>','*/'),
        ('\1','\n'),
        ('\2','<'),
        ('\3','>'))
    for a,b in subs:
        a = a.encode()
        b = b.encode()
        bstr = bstr.replace (a, b)
    return bstr

def isIdent (bstr):
    if re.search (b'_', bstr):
        return True
    elif re.search (b'^[A-Z0-9]*$', bstr):
        return True
    else:
        return False

class Table:
    def __init__ (self, filename):
        self.db = bsddb3.db.DB()
        # FIXME: hardcoded path
        self.db.open ('databases/' + filename, flags=bsddb3.db.DB_RDONLY)

    def exists (self, key):
        return self.db.exists (key)

class DB:
    def __init__ (self):
        self.defs = Table ('definitions.db')
