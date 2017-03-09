#!/usr/bin/python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017  Mikaël Bouillot
#  <mikael.bouillot@free-electrons.com>
#
#  Elixir is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#
#  Elixir is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Elixir.  If not, see <http://www.gnu.org/licenses/>.

from sys import argv
from lib import echo, script, scriptLines
import lib
import data
import os

try:
    dbDir = os.environ['LXR_DATA_DIR']
except KeyError:
    print (argv[0] + ': LXR_DATA_DIR needs to be set')
    exit (1)

db = data.DB (dbDir, readonly=True)

cmd = argv[1]

if cmd == 'versions':
    for p in scriptLines ('list-tags', '-r'):
        if db.vers.exists (p):
            echo (p + b'\n')

elif cmd == 'dir':
    version = argv[2]
    path = argv[3]
    p = script ('get-dir', version, path)
    echo (p)

elif cmd == 'file':
    version = argv[2]
    path = argv[3]
    ext = path[-2:]

    if ext == '.c' or ext == '.h':
        tokens = scriptLines ('tokenize-file', version, path)
        even = True
        for tok in tokens:
            even = not even
            if even and db.defs.exists (tok) and lib.isIdent (tok):
                tok = b'\033[31m' + tok + b'\033[0m'
            else:
                tok = lib.unescape (tok)
            echo (tok)
    else:
        p = script ('get-file', version, path)
        echo (p)

elif cmd == 'ident':
    version = argv[2]
    ident = argv[3]

    if not db.defs.exists (ident):
        print (argv[0] + ': Unknown identifier: ' + ident)
        exit()

    if not db.vers.exists (version):
        print (argv[0] + ': Unknown version: ' + version)
        exit()

    vers = db.vers.get (version).iter()
    defs = db.defs.get (ident).iter (dummy=True)
    # FIXME: see why we can have a discrepancy between defs and refs
    if db.refs.exists (ident):
        refs = db.refs.get (ident).iter (dummy=True)
    else:
        refs = data.RefList().iter (dummy=True)

    id2, type, dline = next (defs)
    id3, rlines = next (refs)

    dBuf = []
    rBuf = []

    for id1, path in vers:
        while id1 > id2:
            id2, type, dline = next (defs)
        while id1 > id3:
            id3, rlines = next (refs)
        while id1 == id2:
            dBuf.append ((path, type, dline))
            id2, type, dline = next (defs)
        if id1 == id3:
            rBuf.append ((path, rlines))

    print ('Defined in', len (dBuf), 'files:')
    for path, type, dline in sorted (dBuf):
        print (path + ': ' + str (dline) + ' (' + type + ')')

    print ('\nReferenced in', len (rBuf), 'files:')
    for path, rlines in sorted (rBuf):
        print (path + ': ' + rlines)

else:
    print (argv[0] + ': Unknown subcommand: ' + cmd)
