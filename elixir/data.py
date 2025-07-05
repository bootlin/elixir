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

from typing import OrderedDict
import berkeleydb
import re
from . import lib
from .lib import autoBytes
import os
import os.path
import errno

# Cache size used by the update script for the largest databases. Tuple of (gigabytes, bytes).
# https://docs.oracle.com/database/bdb181/html/api_reference/C/dbset_cachesize.html
# https://docs.oracle.com/database/bdb181/html/programmer_reference/general_am_conf.html#am_conf_cachesize
CACHESIZE = (2,0)

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

##################################################################################

maxId = 999999999

class DefList:
    '''Stores associations between a blob ID, a type (e.g., "function"),
        a line number and a file family.
        Also stores in which families the ident exists for faster tests.'''
    def __init__(self, data=b'#'):
        data, self.families = data.split(b'#')

        self.entries = OrderedDict()
        tmp_entries = [self.decode_entry(d) for d in deflist_regex.findall(data)]
        tmp_entries.sort(key=lambda x:int(x[0]))
        for id, type, line, family in tmp_entries:
            if id not in self.entries:
                self.entries[id] = [(type, line, family)]
            else:
                self.entries[id].append((type, line, family))

    def decode_entry(self, entry):
        id = int(entry[0])
        type = defTypeR [entry[1].decode()]
        line = int(entry[2])
        family = entry[3].decode()
        return id, type, line, family

    def encode_entry(self, entry):
        return str(entry[0]) + defTypeD[entry[1]] + str(entry[2]) + entry[3]

    def iter(self, dummy=False):
        # Get all element in a list of sublists and sort them
        for id, val in self.entries.items():
            for type, line, family in val:
                yield id, type, line, family
        if dummy:
            yield maxId, None, None, None

    def exists(self, idx, line_num):
        for id, _, line, _ in self.entries:
            if id == idx and int(line) == line_num:
                return True

        return False

    def append(self, id, type, line, family):
        if type not in defTypeD:
            return

        if id not in self.entries:
            self.entries[id] = [(type, line, family)]
        else:
            self.entries[id].append((type, line, family))

        self.add_family(family)

    def pack(self):
        data = ",".join(self.encode_entry((id, *entry)) for id, vals in self.entries.items() for entry in vals)
        return data.encode() + b'#' + self.families

    def add_family(self, family):
        family = family.encode()
        if not family in self.families.split(b','):
            if self.families != b'':
                family = b',' + family
            self.families += family

    def get_families(self):
        return self.families.decode().split(',')

    def get_macros(self):
        return [entry[3] for val in self.entries.values() for entry in val if entry[1] == 'macro']

class PathList:
    '''Stores associations between a blob ID and a file path.
        Inserted by update.py sorted by blob ID.'''
    def __init__(self, data=b''):
        self.data = data

    def iter(self, dummy=False):
        for p in self.data.split(b'\n')[:-1]:
            id, path = p.split(b' ',maxsplit=1)
            id = int(id)
            path = path.decode()
            yield id, path
        if dummy:
            yield maxId, None

    def append(self, id, path):
        p = str(id).encode() + b' ' + path + b'\n'
        self.data += p

    def pack(self):
        return self.data

class RefList:
    '''Stores a mapping from blob ID to list of lines
        and the corresponding family.'''
    def __init__(self, data=b''):
        self.data = data
        self.entries = [self.decode_entry(x.split(b':')) for x in self.data.split(b'\n')[:-1]]
        self.sorted = False

    def decode_entry(self, k):
        return (int(k[0].decode()), k[1].decode(), k[2].decode())

    def iter(self, dummy=False):
        # Split all elements in a list of sublists and sort them
        if not self.sorted:
            self.sorted = True
            self.entries.sort(key=lambda x:int(x[0]))

        for b, c, d in self.entries:
            yield b, c, d
        if dummy:
            yield maxId, None, None

    def append(self, id, lines, family):
        self.sorted = False
        self.entries.append((id, lines, family))

    def pack(self):
        if not self.sorted:
            self.sorted = True
            self.entries.sort(key=lambda x:int(x[0]))

        result = ""
        for id, lines, family in self.entries:
            result += str(id) + ":" + lines + ":" + family + "\n"
        return result.encode()

class BsdDB:
    def __init__(self, filename, readonly, contentType, shared=False, cachesize=None):
        self.filename = filename
        self.db = berkeleydb.db.DB()
        self.flags = berkeleydb.db.DB_THREAD if shared else 0

        self.readonly = readonly
        if self.readonly:
            self.flags |= berkeleydb.db.DB_RDONLY
        else:
            self.flags |= berkeleydb.db.DB_CREATE

        if cachesize is not None:
            self.db.set_cachesize(cachesize[0], cachesize[1])

        self.open()
        self.ctype = contentType

    def open(self):
        if self.readonly:
            self.db.open(self.filename, flags=self.flags)
        else:
            self.db.open(self.filename, flags=self.flags, mode=0o644, dbtype=berkeleydb.db.DB_BTREE)

    def exists(self, key):
        key = autoBytes(key)
        return self.db.exists(key)

    def get(self, key):
        key = autoBytes(key)
        p = self.db.get(key)
        if p is None:
            return None
        p = self.ctype(p)
        return p

    def get_keys(self):
        return self.db.keys()

    def put(self, key, val, sync=False):
        key = autoBytes(key)
        val = autoBytes(val)
        if type(val) is not bytes:
            val = val.pack()
        self.db.put(key, val)
        if sync:
            self.db.sync()

    def sync(self):
        self.db.sync()
    
    def close(self):
        self.db.close()

    def __len__(self):
        return self.db.stat()["nkeys"]

class CachedBsdDB:
    def __init__(self, filename, readonly, contentType, cachesize):
        self.filename = filename
        self.db = None
        self.readonly = readonly

        self.cachesize = cachesize
        self.cache = OrderedDict()

        self.open()

        self.ctype = contentType

    def open(self):
        if self.db is None:
            self.db = berkeleydb.db.DB()

        flags = 0

        if self.readonly:
            flags |= berkeleydb.db.DB_RDONLY
            self.db.open(self.filename, flags=flags)
        else:
            flags |= berkeleydb.db.DB_CREATE
            self.db.open(self.filename, flags=flags, mode=0o644, dbtype=berkeleydb.db.DB_BTREE)

    def exists(self, key):
        if key in self.cache:
            return True

        return self.db.exists(autoBytes(key))

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]

        p = self.db.get(autoBytes(key))
        if p is None:
            return None
        p = self.ctype(p)

        self.cache[key] = p
        self.cache.move_to_end(key)
        if len(self.cache) > self.cachesize:
            old_k, old_v = self.cache.popitem(last=False)
            if not self.readonly:
                self.put_raw(old_k, old_v)

        return p

    def get_keys(self):
        return self.db.keys()

    def put(self, key, val):
        if self.readonly:
            raise Exception("database is readonly")

        self.cache[key] = val
        self.cache.move_to_end(key)
        if len(self.cache) > self.cachesize:
            old_k, old_v = self.cache.popitem(last=False)
            self.put_raw(old_k, old_v)

    def put_raw(self, key, val, sync=False):
        if self.readonly:
            raise Exception("database is readonly")

        key = autoBytes(key)
        val = autoBytes(val)
        if type(val) is not bytes:
            val = val.pack()
        self.db.put(key, val)
        if sync:
            self.db.sync()

    def sync(self):
        if not self.readonly:
            for k, v in self.cache.items():
                self.put_raw(k, v)

        self.db.sync()

    def close(self):
        self.sync()
        self.db.close()
        self.db = None

    def __len__(self):
        return self.db.stat()["nkeys"]

class DB:
    def __init__(self, dir, readonly=True, dtscomp=False, shared=False, update_cache=None):
        if os.path.isdir(dir):
            self.dir = dir
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), dir)

        ro = readonly

        if update_cache:
            db_cls = lambda dir, ro, ctype: CachedBsdDB(dir, ro, ctype, cachesize=update_cache)
        else:
            db_cls = lambda dir, ro, ctype: BsdDB(dir, ro, ctype, shared=shared)

        self.vars = BsdDB(dir + '/variables.db', ro, lambda x: int(x.decode()), shared=shared)
            # Key-value store of basic information
        self.blob = BsdDB(dir + '/blobs.db', ro, lambda x: int(x.decode()), shared=shared)
            # Map hash to sequential integer serial number
        self.hash = BsdDB(dir + '/hashes.db', ro, lambda x: x, shared=shared)
            # Map serial number back to hash
        self.file = BsdDB(dir + '/filenames.db', ro, lambda x: x.decode(), shared=shared)
            # Map serial number to filename
        self.vers = BsdDB(dir + '/versions.db', ro, PathList, shared=shared)
        self.defs = db_cls(dir + '/definitions.db', ro, DefList)
        self.defs_cache = {}
        NOOP = lambda x: x
        self.defs_cache['C'] = BsdDB(dir + '/definitions-cache-C.db', ro, NOOP, shared=shared)
        self.defs_cache['K'] = BsdDB(dir + '/definitions-cache-K.db', ro, NOOP, shared=shared)
        self.defs_cache['D'] = BsdDB(dir + '/definitions-cache-D.db', ro, NOOP, shared=shared)
        self.defs_cache['M'] = BsdDB(dir + '/definitions-cache-M.db', ro, NOOP, shared=shared)
        assert sorted(self.defs_cache.keys()) == sorted(lib.CACHED_DEFINITIONS_FAMILIES)
        self.refs = db_cls(dir + '/references.db', ro, RefList)
        self.docs = db_cls(dir + '/doccomments.db', ro, RefList)
        self.dtscomp = dtscomp
        if dtscomp:
            self.comps = db_cls(dir + '/compatibledts.db', ro, RefList)
            self.comps_docs = db_cls(dir + '/compatibledts_docs.db', ro, RefList)
            # Use a RefList in case there are multiple doc comments for an identifier

    def close(self):
        self.vars.close()
        self.blob.close()
        self.hash.close()
        self.file.close()
        self.vers.close()
        self.defs.close()
        self.defs_cache['C'].close()
        self.defs_cache['K'].close()
        self.defs_cache['D'].close()
        self.defs_cache['M'].close()
        self.refs.close()
        self.docs.close()
        if self.dtscomp:
            self.comps.close()
            self.comps_docs.close()

