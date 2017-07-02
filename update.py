#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017  Mikaël Bouillot
#  <mikael.bouillot@free-electrons.com>
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

from sys import argv
from lib import script, scriptLines
import lib
import data
import os
from data import PathList

try:
    dbDir = os.environ['LXR_DATA_DIR']
except KeyError:
    print (argv[0] + ': LXR_DATA_DIR needs to be set')
    exit (1)

db = data.DB (dbDir, readonly=False)

def updateBlobIDs (tag):
    if db.vars.exists ('numBlobs'):
        idx = db.vars.get ('numBlobs')
    else:
        idx = 0

    blobs = scriptLines ('list-blobs', '-f', tag)

    newBlobs = []
    for blob in blobs:
        hash, filename = blob.split (b' ',maxsplit=1)
        if not db.blob.exists (hash):
            db.blob.put (hash, idx)
            db.hash.put (idx, hash)
            db.file.put (idx, filename)
            newBlobs.append (idx)
            idx += 1
    db.vars.put ('numBlobs', idx)
    return newBlobs

def updateVersions (tag):
    blobs = scriptLines ('list-blobs', '-p', tag)
    buf = []

    for blob in blobs:
        hash, path = blob.split (b' ',maxsplit=1)
        idx = db.blob.get (hash)
        buf.append ((idx, path))

    buf = sorted (buf)
    obj = PathList()
    for idx, path in buf:
        obj.append (idx, path)
    db.vers.put (tag, obj, sync=True)

def updateDefinitions (blobs):
    for blob in blobs:
        if (blob % 100 == 0): print ('D:', blob)
        hash = db.hash.get (blob)
        filename = db.file.get (blob)

        ext = filename[-2:]
        if not (ext == '.c' or ext == '.h'): continue

        lines = scriptLines ('parse-defs', hash, filename)
        for l in lines:
            ident, type, line = l.split (b' ')
            type = type.decode()
            line = int (line.decode())

            if db.defs.exists (ident):
                obj = db.defs.get (ident)
            else:
                obj = data.DefList()

            obj.append (blob, type, line)
            db.defs.put (ident, obj)

def updateReferences (blobs):
    for blob in blobs:
        if (blob % 100 == 0): print ('R:', blob)
        hash = db.hash.get (blob)
        filename = db.file.get (blob)

        ext = filename[-2:]
        if not (ext == '.c' or ext == '.h'): continue

        tokens = scriptLines ('tokenize-file', '-b', hash)
        even = True
        lineNum = 1
        idents = {}
        for tok in tokens:
            even = not even
            if even:
                if db.defs.exists (tok) and lib.isIdent (tok):
                    if tok in idents:
                        idents[tok] += ',' + str(lineNum)
                    else:
                        idents[tok] = str(lineNum)
            else:
                lineNum += tok.count (b'\1')

        for ident, lines in idents.items():
            if db.refs.exists (ident):
                obj = db.refs.get (ident)
            else:
                obj = data.RefList()

            obj.append (blob, lines)
            db.refs.put (ident, obj)

# Main

tagBuf = []
for tag in scriptLines ('list-tags'):
    if not db.vers.exists (tag):
        tagBuf.append (tag)

print ('Found ' + str(len(tagBuf)) + ' new tags')

for tag in tagBuf:
    print (tag.decode(), end=': ')
    newBlobs = updateBlobIDs (tag)
    print (str(len(newBlobs)) + ' new blobs')
    updateVersions (tag)
    updateDefinitions (newBlobs)
    updateReferences (newBlobs)
