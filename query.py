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

from lib import script, scriptLines, decode
import lib
import data
import os
from collections import OrderedDict
from urllib import parse

dts_comp_support = int(script('dts-comp'))

db = data.DB(lib.getDataDir(), readonly=True, dtscomp=dts_comp_support)

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
        previous = None
        tag = ''
        index = 0

        # If we get the same tag twice, we are at the oldest one
        while not db.vers.exists(tag) and previous != tag:
            previous = tag
            tag = decode(script('get-latest', str(index))).rstrip('\n')
            index += 1

        return tag

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

    elif cmd == 'exist':

        # Returns True if the requested file exists, overwise returns False

        version = args[0]
        path = args[1]

        dirname, filename = os.path.split(path)

        entries = decode(script('get-dir', version, dirname)).split("\n")[:-1]
        for entry in entries:
            fname = entry.split(" ")[1]

            if fname == filename:
                return True

        return False

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

        filename = os.path.basename(path)
        family = lib.getFileFamily(filename)

        if family != None:
            buffer = BytesIO()
            tokens = scriptLines('tokenize-file', version, path, family)
            even = True

            prefix = b''
            if family == 'K':
                prefix = b'CONFIG_'

            for tok in tokens:
                even = not even
                tok2 = prefix + tok
                if (even and db.defs.exists(tok2) and
                    (lib.compatibleFamily(db.defs.get(tok2).get_families(), family) or
                    lib.compatibleMacro(db.defs.get(tok2).get_macros(), family))):
                    tok = b'\033[31m' + tok2 + b'\033[0m'
                else:
                    tok = lib.unescape(tok)
                buffer.write(tok)
            return decode(buffer.getvalue())
        else:
            return decode(script('get-file', version, path))

    elif cmd == 'family':
        # Get the family of a given file

        filename = args[0]

        return lib.getFileFamily(filename)

    elif cmd == 'dts-comp':
        # Get state of dts_comp_support

        return dts_comp_support

    elif cmd == 'dts-comp-exists':
        # Check if a dts compatible string exists

        ident = args[0]
        if dts_comp_support:
            return db.comps.exists(ident)
        else:
            return False

    elif cmd == 'keys':
        # Return all keys of a given database
        # /!\ This can take a while /!\

        name = args[0]

        if name == 'vars':
            return db.vars.get_keys()
        elif name == 'blob':
            return db.blob.get_keys()
        elif name == 'hash':
            return db.hash.get_keys()
        elif name == 'file':
            return db.file.get_keys()
        elif name == 'vers':
            return db.vers.get_keys()
        elif name == 'defs':
            return db.defs.get_keys()
        elif name == 'refs':
            return db.refs.get_keys()
        elif name == 'docs':
            return db.docs.get_keys()
        elif name == 'comps' and dts_comp_support:
            return db.comps.get_keys()
        elif name == 'comps_docs' and dts_comp_support:
            return db.comps_docs.get_keys()
        else:
            return []

    elif cmd == 'ident':

        # Returns identifier search results

        version = args[0]
        ident = args[1]
        family = args[2]

        # DT bindings compatible strings are handled differently
        if family == 'B':
            return get_idents_comps(version, ident)
        else:
            return get_idents_defs(version, ident, family)

    else:
        return('Unknown subcommand: ' + cmd + '\n')

def get_idents_comps(version, ident):

    # DT bindings compatible strings are handled differently
    # They are defined in C files
    # Used in DT files
    # Documented in documentation files
    symbol_c = []
    symbol_dts = []
    symbol_docs = []

    ident = parse.quote(ident)

    if not dts_comp_support or not db.comps.exists(ident):
        return symbol_c, symbol_dts, symbol_docs

    files_this_version = db.vers.get(version).iter()
    comps = db.comps.get(ident).iter(dummy=True)

    if db.comps_docs.exists(ident):
        comps_docs = db.comps_docs.get(ident).iter(dummy=True)
    else:
        comps_docs = data.RefList().iter(dummy=True)

    comps_idx, comps_lines, comps_family = next(comps)
    comps_docs_idx, comps_docs_lines, comps_docs_family = next(comps_docs)
    compsCBuf = [] # C/CPP/ASM files
    compsDBuf = [] # DT files
    compsBBuf = [] # DT bindings docs files

    for file_idx, file_path in files_this_version:
        while comps_idx < file_idx:
            comps_idx, comps_lines, comps_family = next(comps)

        while comps_docs_idx < file_idx:
            comps_docs_idx, comps_docs_lines, comps_docs_family = next(comps_docs)

        if comps_idx == file_idx:
            if comps_family == 'C':
                compsCBuf.append((file_path, comps_lines))
            elif comps_family == 'D':
                compsDBuf.append((file_path, comps_lines))

        if comps_docs_idx == file_idx:
            compsBBuf.append((file_path, comps_docs_lines))

    for path, cline in sorted(compsCBuf):
        symbol_c.append(SymbolInstance(path, cline, 'compatible'))

    for path, dlines in sorted(compsDBuf):
        symbol_dts.append(SymbolInstance(path, dlines))

    for path, blines in sorted(compsBBuf):
        symbol_docs.append(SymbolInstance(path, blines))

    return symbol_c, symbol_dts, symbol_docs

def get_idents_defs(version, ident, family):

    symbol_definitions = []
    symbol_references = []
    symbol_doccomments = []

    if not db.defs.exists(ident):
        return symbol_definitions, symbol_references, symbol_doccomments

    if not db.vers.exists(version):
        return symbol_definitions, symbol_references, symbol_doccomments

    files_this_version = db.vers.get(version).iter()
    this_ident = db.defs.get(ident)
    defs_this_ident = this_ident.iter(dummy=True)
    macros_this_ident = this_ident.get_macros()
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

    def_idx, def_type, def_line, def_family = next(defs_this_ident)
    ref_idx, ref_lines, ref_family = next(refs)
    doc_idx, doc_line, doc_family = next(docs)

    dBuf = []
    rBuf = []
    docBuf = []

    for file_idx, file_path in files_this_version:
        # Advance defs, refs, and docs to the current file
        while def_idx < file_idx:
            def_idx, def_type, def_line, def_family = next(defs_this_ident)
        while ref_idx < file_idx:
            ref_idx, ref_lines, ref_family = next(refs)
        while doc_idx < file_idx:
            doc_idx, doc_line, doc_family = next(docs)

        # Copy information about this identifier into dBuf, rBuf, and docBuf.
        while def_idx == file_idx:
            if (def_family == family or family == 'A'
                or lib.compatibleMacro(macros_this_ident, family)):
                dBuf.append((file_path, def_type, def_line))
            def_idx, def_type, def_line, def_family = next(defs_this_ident)

        if ref_idx == file_idx:
            if lib.compatibleFamily(family, ref_family) or family == 'A':
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

def cmd_ident(version, ident, family, **kwargs):
    symbol_definitions, symbol_references, symbol_doccomments = query("ident", version, ident, family)
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
    ident_subparser.add_argument('family', type=str, help="The file family requested")
    ident_subparser.set_defaults(func=cmd_ident)

    file_subparser = subparsers.add_parser('file', help="Get a source file")
    file_subparser.add_argument('path', type=str, help="The path of the source file")
    file_subparser.set_defaults(func=cmd_file)

    args = parser.parse_args()
    args.func(**vars(args))
