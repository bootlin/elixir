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

def isIdent (bstr):
    if re.search (b'_', bstr):
        return True
    elif re.search (b'^[A-Z0-9]*$', bstr):
        return True
    else:
        return False

def autoBytes (arg):
    if type (arg) is str:
        arg = arg.encode()
    return arg

##########################################################################

from struct import pack, unpack
from binascii import hexlify, unhexlify
from io import BytesIO

def pack_hash (a):
	a = a.encode ('ascii')
	a = unhexlify (a)
	a = pack ('20s', a)
	return a

def unpack_hash (a):
	a = unpack ('20s', a)
	a = a[0]
	a = hexlify (a)
	a = a.decode ('ascii')
	return a

def pack_int (a):
	a = pack ('>L', a)
	return a

def unpack_int (a):
	a = unpack ('>L', a)
	a = a[0]
	return a

def append_reflist (a, idx, string):
	idx = pack_int (idx)
	a = a + idx + string + b'E'
	return a

#def unpack_reflist (a):
#	size = len (a)
#	s = BytesIO (a)
#	res = []
#	while s.tell() < size:
#		b = s.read (4)
#		b = unpack_int (b)
#
#		# Reading byte by byte isn't optimal
#		t = BytesIO()
#		d = s.read (1)
#		while d != b'E':
#			t.write (d)
#			d = s.read (1)
#		c = t.getvalue()
#		t.close()
#
#		res.append ((b,c))
#	s.close()
#	return res

##################################################################################

defTypeD = {
    'define': 'd',
    'enum': 'e',
    'enumerator': 'E',
    'function': 'f',
    'label': 'l',
    'macro': 'M',
    'member': 'm',
    'struct': 's',
    'typedef': 't',
    'union': 'u',
    'variable': 'v' }

defTypeR = {
    'd': 'define',
    'e': 'enum',
    'E': 'enumerator',
    'f': 'function',
    'l': 'label',
    'M': 'macro',
    'm': 'member',
    's': 'struct',
    't': 'typedef',
    'u': 'union',
    'v': 'variable' }

##################################################################################

class DefList:
    def __init__ (self, data):
        self.data = data

    def iter (self):
        for p in self.data.split (b','):
            p = re.search (b'(\d*)(\w)(\d*)', p)
            id, type, line = p.groups()
            id = int (id)
            type = defTypeR [type.decode()]
            line = int (line)
            yield (id, type, line)

class PathList:
    def __init__ (self, data):
        self.data = data

    def iter (self):
        for p in self.data.split (b'\n'):
            p = re.search (b'(\d*)\t(.*)$', p)
            id, path = p.groups()
            id = int (id)
            path = path.decode()
            yield (id, path)

from io import BytesIO

class RefList:
    def __init__ (self, data):
        self.data = data

    def iter (self):
        size = len (self.data)
        s = BytesIO (self.data)
        while s.tell() < size:
            b = s.read (4)
            b = unpack_int (b)

            # Reading byte by byte isn't optimal
            t = BytesIO()
            d = s.read (1)
            while d != b'E':
                t.write (d)
                d = s.read (1)
            c = t.getvalue()
            c = c.decode()
            t.close()
            yield (b, c)
        s.close()

import os.path

class DirDB:
    def __init__ (self, dirname, contentType):
        # FIXME: hardcoded path
        self.path = 'databases/' + dirname + '/'
        self.ctype = contentType

    def exists (self, key):
        return os.path.isfile (self.path + 'v' + key)

    def get (self, key):
        f = open (self.path + 'v' + key)
        data = f.read()
        data = data.encode()
        f.close()
        return self.ctype (data)

class BsdDB:
    def __init__ (self, filename, contentType):
        self.db = bsddb3.db.DB()
        # FIXME: hardcoded path
        self.db.open ('databases/' + filename, flags=bsddb3.db.DB_RDONLY)
        self.ctype = contentType

    def exists (self, key):
        key = autoBytes (key)
        return self.db.exists (key)

    def get (self, key):
        key = autoBytes (key)
        p = self.db.get (key)
        p = self.ctype (p)
        return p

class DB:
    def __init__ (self):
        self.vers = DirDB ('versions', PathList)
        self.defs = BsdDB ('definitions.db', DefList)
        self.refs = BsdDB ('identrefs.db', RefList)

