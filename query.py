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

from lib import script, scriptLines
import lib
import data
import os

try:
    dbDir = os.environ['LXR_DATA_DIR']
except KeyError:
    print ('LXR_DATA_DIR needs to be set')
    exit (1)

db = data.DB (dbDir, readonly=True)

from io import BytesIO

def query (cmd, *args):
    buffer = BytesIO()

    def echo (arg):
        buffer.write (arg)

    if cmd == 'versions':
        for tag in scriptLines ("list-tags", "-h"):
            if db.vers.exists (tag):
                echo (tag + b'\n')

    elif cmd == 'latest':
        p = script ("get-latest")
        echo (p)

    elif cmd == 'type':
        version = args[0]
        path = args[1]
        p = script ('get-type', version, path)
        echo (p)

    elif cmd == 'dir':
        version = args[0]
        path = args[1]
        p = script ('get-dir', version, path)
        echo (p)

    elif cmd == 'file':
        version = args[0]
        path = args[1]
        ext = os.path.splitext(path)[1]

        if version == 'latest':
            version = script ("get-latest")
        if ext in ['.c', '.cc', '.cpp', '.h']:
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
        version = args[0]
        ident = args[1]

        if not db.defs.exists (ident):
            echo (('Unknown identifier: ' + ident + '\n').encode())
            return buffer.getvalue()

        if not db.vers.exists (version):
            echo (('Unknown version: ' + version + '\n').encode())
            return buffer.getvalue()

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

        echo (('Defined in ' + str(len(dBuf)) + ' files:\n').encode())
        for path, type, dline in sorted (dBuf):
            echo ((path + ': ' + str (dline) + ' (' + type + ')\n').encode())

        echo (('\nReferenced in ' + str(len(rBuf)) + ' files:\n').encode())
        for path, rlines in sorted (rBuf):
            echo ((path + ': ' + rlines + '\n').encode())

    else:
        echo (('Unknown subcommand: ' + cmd + '\n').encode())

    return buffer.getvalue()

if __name__ == "__main__":
    import sys

    output = query (*(sys.argv[1:]))
    sys.stdout.buffer.write (output)
