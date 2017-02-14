#!/usr/bin/python3

import bsddb3
from io import BytesIO
import re
from lib import autoBytes
import os.path

##################################################################################

defTypeR = {
    'd': 'define',
    'e': 'enum',
    'E': 'enumerator',
    'f': 'function',
    'l': 'label',
    'M': 'macro',
    'm': 'member',
    'p': 'prototype',
    's': 'struct',
    't': 'typedef',
    'u': 'union',
    'v': 'variable' }

defTypeD = {v: k for k, v in defTypeR.items()}

##################################################################################

maxId = 999999999

class DefList:
    def __init__ (self, data=b''):
        self.data = data

    def iter (self, dummy=False):
        for p in self.data.split (b','):
            p = re.search (b'(\d*)(\w)(\d*)', p)
            id, type, line = p.groups()
            id = int (id)
            type = defTypeR [type.decode()]
            line = int (line)
            yield (id, type, line)
        if dummy:
            yield (maxId, None, None)

    def append (self, id, type, line):
        if type not in defTypeD:
            return
        p = str(id) + defTypeD[type] + str(line)
        if self.data != b'':
            p = ',' + p
        self.data += p.encode()

    def pack (self):
        return self.data

class PathList:
    def __init__ (self, data=b''):
        self.data = data

    def iter (self, dummy=False):
        for p in self.data.split (b'\n'):
            if (p == b''): continue
            id, path = p.split (b' ')
            id = int (id)
            path = path.decode()
            yield (id, path)
        if dummy:
            yield (maxId, None)

    def append (self, id, path):
        p = str(id).encode() + b' ' + path
        self.data = self.data + p + b'\n'

    def pack (self):
        return self.data

from io import BytesIO

class RefList:
    def __init__ (self, data=b''):
        self.data = data

    def iter (self, dummy=False):
        size = len (self.data)
        s = BytesIO (self.data)
        while s.tell() < size:
            line = s.readline()
            line = line [:-1]
            b,c = line.split (b':')
            b = int (b.decode())
            c = c.decode()
            yield (b, c)
        s.close()
        if dummy:
            yield (maxId, None)

    def append (self, id, lines):
        p = str(id) + ':' + lines + '\n'
        self.data += p.encode()

    def pack (self):
        return self.data

class BsdDB:
    def __init__ (self, filename, readonly, contentType):
        self.filename = filename
        self.db = bsddb3.db.DB()
        if readonly:
            self.db.open (filename, flags=bsddb3.db.DB_RDONLY)
        else:
            self.db.open (filename,
                flags=bsddb3.db.DB_CREATE,
                dbtype=bsddb3.db.DB_BTREE)
        self.ctype = contentType

    def exists (self, key):
        key = autoBytes (key)
        return self.db.exists (key)

    def get (self, key):
        key = autoBytes (key)
        p = self.db.get (key)
        p = self.ctype (p)
        return p

    def put (self, key, val):
        key = autoBytes (key)
        val = autoBytes (val)
        if type (val) is not bytes:
            val = val.pack()
        self.db.put (key, val)

class DB:
    def __init__ (self, dir, readonly=True):
        if os.path.isdir (dir):
            self.dir = dir
        else:
            raise FileNotFoundError

        ro = readonly

        self.vars = BsdDB (dir + '/variables.db', ro, lambda x: int (x.decode()) )
        self.blob = BsdDB (dir + '/blobs.db', ro, lambda x: int (x.decode()) )
        self.hash = BsdDB (dir + '/hashes.db', ro, lambda x: x )
        self.file = BsdDB (dir + '/filenames.db', ro, lambda x: x.decode() )
        self.vers = BsdDB (dir + '/versions.db', ro, PathList)
        self.defs = BsdDB (dir + '/definitions.db', ro, DefList)
        self.refs = BsdDB (dir + '/references.db', ro, RefList)
