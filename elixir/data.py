#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017--2020 Mikaël Bouillot <mikael.bouillot@bootlin.com>
#  and contributors
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

import berkeleydb
import re
from .lib import autoBytes
import os
import os.path
import errno

import msgpack._cmsgpack

deflist_regex = re.compile(b'(\d*)(\w)(\d*)(\w),?')
deflist_macro_regex = re.compile('\dM\d+(\w)')

##################################################################################

defTypeR = {
    'c': 'config',
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
    'v': 'variable',
    'x': 'externvar'}

defTypeD = {v: k for k, v in defTypeR.items()}

defTypeToInt = {
    'config': 0,
    'define': 1,
    'enum': 2,
    'enumerator': 3,
    'function': 4,
    'label': 5,
    'macro': 6,
    'member': 7,
    'prototype': 8,
    'struct': 9,
    'typedef': 10,
    'union': 11,
    'variable': 12,
    'externvar': 13
}

intToDefType = {v: k for k, v in defTypeToInt.items()}

familyToInt = {
    'A': 0,
    'B': 1,
    'C': 2,
    'D': 3,
    'K': 4,
    'M': 5,
}

intToFamily = {v: k for k, v in familyToInt.items()}

##################################################################################

maxId = 999999999

class DefList:
    '''Stores associations between a blob ID, a type (e.g., "function"),
        a line number and a file family.
        Also stores in which families the ident exists for faster tests.'''
    def __init__(self, data: bytes | None = None):
        if data is not None:
            parsed_data = msgpack.loads(data)
            self.entries = parsed_data[0]
            self.families = parsed_data[1]
        else:
            self.entries = []
            self.families = ""

    def iter(self, dummy=False):
        # return ((id, defTypeR[type], line, family) for (id, type, line, family) in self.data)

        self.entries.sort(key=lambda x: x[0])

        for id, type, line, family in self.entries:
            yield id, intToDefType[type], line, intToFamily[family]

        if dummy:
            yield maxId, None, None, None

    def append(self, id: int, type: str, line: int, family: str):
        # if family not in self.family: self.family.append(family)
        # self.data.append((id, defTypeD[type], line, family))

        if type not in defTypeD:
            return

        self.entries.append((id, defTypeToInt[type], line, familyToInt[family]))

        if family not in self.families:
            self.families += family

    def pack(self):
        return msgpack.dumps([self.entries, self.families])

    def get_families(self):
        return self.families

    def get_macros(self):
        return [intToFamily[family] for _, typ, _, family in self.entries if typ == defTypeToInt['macro']]

class PathList:
    '''Stores associations between a blob ID and a file path.
        Inserted by update.py sorted by blob ID.'''
    def __init__(self, data: bytes | None=None):
        if data is not None:
            # [(id, path)]
            self.data = msgpack.loads(data)
        else:
            self.data = []

    def iter(self, dummy=False):
        for id, path in self.data:
            yield id, path
        if dummy:
            yield maxId, None

    def append(self, id: int, path: str):
        self.data.append((id, path))

    def pack(self):
        return msgpack.dumps(self.data)

class RefList:
    '''Stores a mapping from blob ID to list of lines
        and the corresponding family.'''
    def __init__(self, data=None):
        # {(blob_id, family): [line]}
        if data is not None:
            self.data = msgpack.loads(data, strict_map_key=False)
        else:
            self.data = {}

    def iter(self, dummy=False):
        # Split all elements in a list of sublists and sort them
        for id, family_dict in self.data.items():
            for family, lines in family_dict.items():
                yield id, lines, family
        if dummy:
            yield maxId, None, None

    def append(self, id, lines, family):
        if id not in self.data:
            self.data[id] = {}
        if family not in self.data[id]:
            self.data[id][family] = []

        self.data[id][family] += lines

    def pack(self):
        return msgpack.dumps(self.data)

class BsdDB:
    def __init__(self, filename, readonly, contentType, shared=False):
        self.filename = filename
        self.db = berkeleydb.db.DB()
        flags = berkeleydb.db.DB_THREAD if shared else 0

        if readonly:
            flags |= berkeleydb.db.DB_RDONLY
            self.db.open(filename, flags=flags)
        else:
            flags |= berkeleydb.db.DB_CREATE
            self.db.open(filename, flags=flags, mode=0o644, dbtype=berkeleydb.db.DB_BTREE)
        self.ctype = contentType

    def exists(self, key: str|bytes|int):
        if type(key) is str:
            key = key.encode()
        elif type(key) is int:
            key = msgpack.dumps(key)

        return self.db.exists(key)

    def get(self, key: str|bytes|int):
        if type(key) is str:
            key = key.encode()
        elif type(key) is int:
            key = msgpack.dumps(key)

        p = self.db.get(key)
        if p is not None:
            if self.ctype is None:
                return msgpack.loads(p)
            else:
                return self.ctype(p)
        else:
            return None

    def get_keys(self):
        return self.db.keys()

    def put(self, key: str|bytes|int, val, sync=False):
        if type(key) is str:
            key = key.encode()
        elif type(key) is int:
            key = msgpack.dumps(key)

        if self.ctype is None:
            val = msgpack.dumps(val)
        else:
            val = val.pack()

        self.db.put(key, val)
        if sync:
            self.db.sync()

    def close(self):
        self.db.close()

class DB:
    def __init__(self, dir, readonly=True, dtscomp=False, shared=False):
        if os.path.isdir(dir):
            self.dir = dir
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), dir)

        ro = readonly

        self.vars = BsdDB(dir + '/variables.db', ro, shared=shared)
            # Key-value store of basic information
        self.blob = BsdDB(dir + '/blobs.db', ro, shared=shared)
            # Map hash to sequential integer serial number
        self.hash = BsdDB(dir + '/hashes.db', ro, shared=shared)
            # Map serial number back to hash
        self.file = BsdDB(dir + '/filenames.db', ro, shared=shared)
            # Map serial number to filename
        self.vers = BsdDB(dir + '/versions.db', ro, PathList, shared=shared)
        self.defs = BsdDB(dir + '/definitions.db', ro, DefList, shared=shared)
        self.refs = BsdDB(dir + '/references.db', ro, RefList, shared=shared)
        self.docs = BsdDB(dir + '/doccomments.db', ro, RefList, shared=shared)
        self.dtscomp = dtscomp
        if dtscomp:
            self.comps = BsdDB(dir + '/compatibledts.db', ro, RefList, shared=shared)
            self.comps_docs = BsdDB(dir + '/compatibledts_docs.db', ro, RefList, shared=shared)
            # Use a RefList in case there are multiple doc comments for an identifier

    def close(self):
        self.vars.close()
        self.blob.close()
        self.hash.close()
        self.file.close()
        self.vers.close()
        self.defs.close()
        self.refs.close()
        self.docs.close()
        if self.dtscomp:
            self.comps.close()
            self.comps_docs.close()

