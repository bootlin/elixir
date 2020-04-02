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
from collections import OrderedDict

db = data.DB(lib.getDataDir(), readonly=True)

from io import BytesIO

class SymbolInstance(object):
    def __init__(self, path, line, type=None):
        self.path = path
        self.line = line
        self.type = type

    def __repr__(self):
        type_repr = ""
        if self.type:
            type_repr = f" , type: {self.type}"

        return f"Symbol in path: {self.path}, line: {self.line}" + type_repr

    def __str__(self):
        return self.__repr__()

def decode(byte_object):
    # decode('ascii') fails on special chars
    # FIXME: major hack until we handle everything as bytestrings
    try:
        return byte_object.decode('utf-8')
    except UnicodeDecodeError:
        return byte_object.decode('iso-8859-1')

def query(cmd, *args):
    if cmd == 'versions':

        # Returns the list of indexed versions in the following format:
        # topmenu submenu tag
        # Example: v3 v3.1 v3.1-rc10
        versions = OrderedDict()

        for line in scriptLines('list-tags', '-h'):
            taginfo = decode(line).split(' ')
            num = len(taginfo)
            topmenu, submenu = 'FIXME', 'FIXME'

            if (num == 1):
                tag, = taginfo
            elif (num == 2):
                submenu,tag = taginfo
            elif (num ==3):
                topmenu,submenu,tag = taginfo

            if db.vers.exists(tag):
                if topmenu not in versions:
                    versions[topmenu] = OrderedDict()
                if submenu not in versions[topmenu]:
                    versions[topmenu][submenu] = []
                versions[topmenu][submenu].append(tag)

        return versions

    elif cmd == 'latest':

        # Returns the tag considered as the latest one
        # TODO: this latest tag may have just been retrieved
        # in the git repository and may not have been indexed yet
        # This could results in failed queries

        return decode(script('get-latest')).rstrip('\n')

    elif cmd == 'type':

        # Returns the type (blob or tree) associated to
        # the given path. Example:
        # > ./query.py type v3.1-rc10 /Makefile
        # blob
        # > ./query.py type v3.1-rc10 /arch
        # tree

        version = args[0]
        path = args[1]
        return decode(script('get-type', version, path)).strip()

    elif cmd == 'dir':

        # Returns the contents (trees or blobs) of the specified directory
        # Example: ./query.py dir v3.1-rc10 /arch

        version = args[0]
        path = args[1]
        entries_str =  decode(script('get-dir', version, path))
        return entries_str.split("\n")[:-1]

    elif cmd == 'file':

        # Returns the contents of the specified file
        # Tokens are marked for further processing
        # Example: ./query.py file v3.1-rc10 /Makefile

        version = args[0]
        path = args[1]

        if lib.hasSupportedExt(path):
            buffer = BytesIO()
            tokens = scriptLines('tokenize-file', version, path)
            even = True
            for tok in tokens:
                even = not even
                if even and db.defs.exists(tok) and lib.isIdent(tok):
                    tok = b'\033[31m' + tok + b'\033[0m'
                else:
                    tok = lib.unescape(tok)
                buffer.write(tok)
            return decode(buffer.getvalue())
        else:
            return decode(script('get-file', version, path))

    elif cmd == 'ident':

        # Returns identifier search results

        version = args[0]
        ident = args[1]

        symbol_definitions = []
        symbol_references = []
        symbol_doccomments = []

        if not db.defs.exists(ident):
            return symbol_definitions, symbol_references, symbol_doccomments

        if not db.vers.exists(version):
            return symbol_definitions, symbol_references, symbol_doccomments

        files_this_version = db.vers.get(version).iter()
        defs_this_ident = db.defs.get(ident).iter(dummy=True)
        # FIXME: see why we can have a discrepancy between defs_this_ident and refs
        if db.refs.exists(ident):
            refs = db.refs.get(ident).iter(dummy=True)
        else:
            refs = data.RefList().iter(dummy=True)

        if db.docs.exists(ident):
            docs = db.docs.get(ident).iter(dummy=True)
        else:
            docs = data.RefList().iter(dummy=True)

        # vers, defs, refs, and docs are all populated by update.py in order of
        # idx, and there is a one-to-one mapping between blob hashes and idx
        # values.  Therefore, we can sequentially step through the defs, refs,
        # and docs for each file in a version.

        def_idx, def_type, def_line = next(defs_this_ident)
        ref_idx, ref_lines = next(refs)
        doc_idx, doc_line = next(docs)

        dBuf = []
        rBuf = []
        docBuf = []

        for file_idx, file_path in files_this_version:
            # Advance defs, refs, and docs to the current file
            while def_idx < file_idx:
                def_idx, def_type, def_line = next(defs_this_ident)
            while ref_idx < file_idx:
                ref_idx, ref_lines = next(refs)
            while doc_idx < file_idx:
                doc_idx, doc_line = next(docs)

            # Copy information about this identifier into dBuf, rBuf, and docBuf.
            while def_idx == file_idx:
                dBuf.append((file_path, def_type, def_line))
                def_idx, def_type, def_line = next(defs_this_ident)

            if ref_idx == file_idx:
                rBuf.append((file_path, ref_lines))

            if doc_idx == file_idx: # TODO should this be a `while`?
                docBuf.append((file_path, doc_line))


        for path, type, dline in sorted(dBuf):
            symbol_definitions.append(SymbolInstance(path, dline, type))

        for path, rlines in sorted(rBuf):
            symbol_references.append(SymbolInstance(path, rlines))

        for path, docline in sorted(docBuf):
            symbol_doccomments.append(SymbolInstance(path, docline))

        return symbol_definitions, symbol_references, symbol_doccomments

    else:
        return('Unknown subcommand: ' + cmd + '\n')

def cmd_ident(version, ident, **kwargs):
    symbol_definitions, symbol_references, symbol_doccomments = query("ident", version, ident)
    print("Symbol Definitions:")
    for symbol_definition in symbol_definitions:
        print(symbol_definition)

    print("\nSymbol References:")
    for symbol_reference in symbol_references:
        print(symbol_reference)

    print("\nDocumented in:")
    for symbol_doccomment in symbol_doccomments:
        print(symbol_doccomment)

def cmd_file(version, path, **kwargs):
    code = query("file", version, path)
    print(code)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("version", help="The version of the project", type=str, default="latest")
    subparsers = parser.add_subparsers()

    ident_subparser = subparsers.add_parser('ident', help="Get definitions and references of an identifier")
    ident_subparser.add_argument('ident', type=str, help="The name of the identifier")
    ident_subparser.set_defaults(func=cmd_ident)

    file_subparser = subparsers.add_parser('file', help="Get a source file")
    file_subparser.add_argument('path', type=str, help="The path of the source file")
    file_subparser.set_defaults(func=cmd_file)

    args = parser.parse_args()
    args.func(**vars(args))
