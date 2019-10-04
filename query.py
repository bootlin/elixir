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

db = data.DB (lib.getDataDir(), readonly=True)

from io import BytesIO

class SymbolInstance(object):
    def __init__(self, path, line, type=None):
        self.path = path
        self.line = line
        self.type = type


def query (cmd, *args):
    buffer = BytesIO()

    def echo (arg):
        buffer.write (arg)

    if cmd == 'versions':

        # Returns the list of indexed versions in the following format:
        # topmenu submenu tag
        # Example: v3 v3.1 v3.1-rc10

        for p in scriptLines ('list-tags', '-h'):
            if db.vers.exists (p.split(b' ')[2]):
                echo (p + b'\n')

    elif cmd == 'latest':

        # Returns the tag considered as the latest one
        # TODO: this latest tag may have just been retrieved
        # in the git repository and may not have been index yet
        # This could results in failed queries

        p = script ('get-latest')
        echo (p)

    elif cmd == 'type':

        # Returns the type (blob or tree) associated to
        # the given path. Example:
        # > ./query.py type v3.1-rc10 /Makefile
        # blob
        # > ./query.py type v3.1-rc10 /arch
        # tree

        version = args[0]
        path = args[1]
        p = script ('get-type', version, path)
        echo (p)

    elif cmd == 'dir':

	# Returns the contents (trees or blobs) of the specified directory
	# Example: ./query.py dir v3.1-rc10 /arch

        version = args[0]
        path = args[1]
        p = script ('get-dir', version, path)
        echo (p)

    elif cmd == 'file':

	# Returns the contents of the specified file
        # Tokens are marked for further processing
        # Example: ./query.py file v3.1-rc10 /Makefile

        version = args[0]
        path = args[1]
        ext = os.path.splitext(path)[1]

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

	# Returns identifier search results

        version = args[0]
        ident = args[1]

        symbol_definitions = []
        symbol_references = []

        if not db.defs.exists (ident):
            return symbol_definitions, symbol_references

        if not db.vers.exists (version):
            return symbol_definitions, symbol_references

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

        for path, type, dline in sorted (dBuf):
            symbol_definitions.append(SymbolInstance(path, dline, type))

        for path, rlines in sorted (rBuf):
            symbol_references.append(SymbolInstance(path, rlines))

        return symbol_definitions, symbol_references

    else:
        echo (('Unknown subcommand: ' + cmd + '\n').encode())

    return buffer.getvalue()

if __name__ == "__main__":
    import sys

    output = query (*(sys.argv[1:]))
    sys.stdout.buffer.write (output)
