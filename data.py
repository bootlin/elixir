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

import bsddb3
from io import BytesIO
import re
from lib import autoBytes
import os
import os.path
import errno

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
    '''Stores associations between a blob ID, a type (e.g., "function"),
        and a line number.'''
    def __init__(self, data=b''):
        self.data = data

    def iter(self, dummy=False):
        for p in self.data.split(b','):
            p = re.search(b'(\d*)(\w)(\d*)', p)
            id, type, line = p.groups()
            id = int(id)
            type = defTypeR [type.decode()]
            line = int(line)
            yield(id, type, line)
        if dummy:
            yield(maxId, None, None)

    def append(self, id, type, line):
        if type not in defTypeD:
            return
        p = str(id) + defTypeD[type] + str(line)
        if self.data != b'':
            p = ',' + p
        self.data += p.encode()

    def pack(self):
        return self.data

class PathList:
    '''Stores associations between a blob ID and a file path.
        Inserted by update.py sorted by blob ID.'''
    def __init__(self, data=b''):
        self.data = data

    def iter(self, dummy=False):
        for p in self.data.split(b'\n'):
            if (p == b''): continue
            id, path = p.split(b' ',maxsplit=1)
            id = int(id)
            path = path.decode()
            yield(id, path)
        if dummy:
            yield(maxId, None)

    def append(self, id, path):
        p = str(id).encode() + b' ' + path
        self.data = self.data + p + b'\n'

    def pack(self):
        return self.data

class RefList:
    '''Stores a mapping from blob ID to list of lines.'''
    def __init__(self, data=b''):
        self.data = data

    def iter(self, dummy=False):
        size = len(self.data)
        s = BytesIO(self.data)
        while s.tell() < size:
            line = s.readline()
            line = line [:-1]
            b,c = line.split(b':')
            b = int(b.decode())
            c = c.decode()
            yield(b, c)
        s.close()
        if dummy:
            yield(maxId, None)

    def append(self, id, lines):
        p = str(id) + ':' + lines + '\n'
        self.data += p.encode()

    def pack(self):
        return self.data

class BsdDB:
    def __init__(self, filename, readonly, contentType):
        self.filename = filename
        self.db = bsddb3.db.DB()
        if readonly:
            self.db.open(filename, flags=bsddb3.db.DB_RDONLY)
        else:
            self.db.open(filename,
                flags=bsddb3.db.DB_CREATE,
                mode=0o644,
                dbtype=bsddb3.db.DB_BTREE)
        self.ctype = contentType

    def exists(self, key):
        key = autoBytes(key)
        return self.db.exists(key)

    def get(self, key):
        key = autoBytes(key)
        p = self.db.get(key)
        p = self.ctype(p)
        return p

    def put(self, key, val, sync=False):
        key = autoBytes(key)
        val = autoBytes(val)
        if type(val) is not bytes:
            val = val.pack()
        self.db.put(key, val)
        if sync:
            self.db.sync()

class DB:
    def __init__(self, dir, readonly=True):
        if os.path.isdir(dir):
            self.dir = dir
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), dir)

        ro = readonly

        self.vars = BsdDB(dir + '/variables.db', ro, lambda x: int(x.decode()) )
            # Key-value store of basic information
        self.blob = BsdDB(dir + '/blobs.db', ro, lambda x: int(x.decode()) )
            # Map hash to sequential integer serial number
        self.hash = BsdDB(dir + '/hashes.db', ro, lambda x: x )
            # Map serial number back to hash
        self.file = BsdDB(dir + '/filenames.db', ro, lambda x: x.decode() )
            # Map serial number to filename
        self.vers = BsdDB(dir + '/versions.db', ro, PathList)
        self.defs = BsdDB(dir + '/definitions.db', ro, DefList)
        self.refs = BsdDB(dir + '/references.db', ro, RefList)
        self.docs = BsdDB(dir + '/doccomments.db', ro, RefList)
            # Use a RefList in case there are multiple doc comments for an identifier
