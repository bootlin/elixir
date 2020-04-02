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

# Throughout, an "idx" is the sequential number associated with a blob.
# This is different from that blob's Git hash.

from sys import argv
from lib import scriptLines
import lib
import data
import os
from data import PathList

verbose = False

db = data.DB(lib.getDataDir(), readonly=False)

# Store new blobs hashed and file names (without path) for new tag

def updateBlobIDs(tag):

    if db.vars.exists('numBlobs'):
        idx = db.vars.get('numBlobs')
    else:
        idx = 0

    # Get blob hashes and associated file names (without path)
    blobs = scriptLines('list-blobs', '-f', tag)

    newIdxes = []
    for blob in blobs:
        hash, filename = blob.split(b' ',maxsplit=1)
        if not db.blob.exists(hash):
            db.blob.put(hash, idx)
            db.hash.put(idx, hash)
            db.file.put(idx, filename)
            newIdxes.append(idx)
            if verbose:
                print(f"New blob #{idx} {hash}:{filename}")
            idx += 1
    db.vars.put('numBlobs', idx)
    return newIdxes

def updateVersions(tag):

    # Get blob hashes and associated file paths
    blobs = scriptLines('list-blobs', '-p', tag)
    buf = []

    for blob in blobs:
        hash, path = blob.split(b' ', maxsplit=1)
        idx = db.blob.get(hash)
        buf.append((idx, path))

    buf = sorted(buf)
    obj = PathList()
    for idx, path in buf:
        obj.append(idx, path)
        if verbose:
            print(f"Tag {tag}: adding #{idx} {path}")
    db.vers.put(tag, obj, sync=True)

def updateDefinitions(idxes):
    for idx in idxes:
        if (idx % 1000 == 0): progress('defs: ' + str(idx))
        hash = db.hash.get(idx)
        filename = db.file.get(idx)

        if not lib.hasSupportedExt(filename): continue

        lines = scriptLines('parse-defs', hash, filename)
        for l in lines:
            ident, type, line = l.split(b' ')
            type = type.decode()
            line = int(line.decode())

            if db.defs.exists(ident):
                obj = db.defs.get(ident)
            else:
                obj = data.DefList()

            obj.append(idx, type, line)
            if verbose:
                print(f"def {type} {ident} in #{idx} @ {line}");
            db.defs.put(ident, obj)

def updateReferences(idxes):
    for idx in idxes:
        if (idx % 1000 == 0): progress('refs: ' + str(idx))
        hash = db.hash.get(idx)
        filename = db.file.get(idx)

        if not lib.hasSupportedExt(filename): continue

        tokens = scriptLines('tokenize-file', '-b', hash)
        even = True
        lineNum = 1
        idents = {}
        for tok in tokens:
            even = not even
            if even:
                if db.defs.exists(tok) and lib.isIdent(tok):
                    if tok in idents:
                        idents[tok] += ',' + str(lineNum)
                    else:
                        idents[tok] = str(lineNum)
            else:
                lineNum += tok.count(b'\1')

        for ident, lines in idents.items():
            if db.refs.exists(ident):
                obj = db.refs.get(ident)
            else:
                obj = data.RefList()

            obj.append(idx, lines)
            if verbose:
                print(f"ref: {ident} in #{idx} @ {lines}");
            db.refs.put(ident, obj)

def updateDocComments(idxes):
    for idx in idxes:
        if (idx % 1000 == 0): progress('docs: ' + str(idx))
        hash = db.hash.get(idx)
        filename = db.file.get(idx)

        if not lib.hasSupportedExt(filename): continue

        lines = scriptLines('parse-docs', hash, filename)
        for l in lines:
            ident, line = l.split(b' ')
            line = int(line.decode())

            if db.docs.exists(ident):
                obj = db.docs.get(ident)
            else:
                obj = data.RefList()

            obj.append(idx, str(line))
            if verbose:
                print(f"doc: {ident} in #{idx} @ {line}");
            db.docs.put(ident, obj)

def progress(msg):
    print('{} - {} ({:.0%})'.format(project, msg, tagCount/numTags))

# Main

tagBuf = []
for tag in scriptLines('list-tags'):
    if not db.vers.exists(tag):
        tagBuf.append(tag)

numTags = len(tagBuf)
tagCount = 0
project = lib.currentProject()

print(project + ' - found ' + str(len(tagBuf)) + ' new tags')

for tag in tagBuf:
    tagCount +=1
    newIdxes = updateBlobIDs(tag)
    progress(tag.decode() + ': ' + str(len(newIdxes)) + ' new blobs')
    updateVersions(tag)
    updateDefinitions(newIdxes)
    updateReferences(newIdxes)
    updateDocComments(newIdxes)
