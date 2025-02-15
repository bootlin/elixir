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

from .lib import script, scriptLines, decode
from . import lib
from . import data
import os
from collections import OrderedDict
from urllib import parse

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

# Returns a Query class instance or None if project data directory does not exist
# basedir: absolute path to parent directory of all project data directories, ex. "/srv/elixir-data/"
# project: name of the project, directory in basedir, ex. "linux"
def get_query(basedir, project):
    datadir = basedir + '/' + project + '/data'
    repodir = basedir + '/' + project + '/repo'

    if not os.path.exists(datadir) or not os.path.exists(repodir):
        return None

    return Query(datadir, repodir)

class Query:
    def __init__(self, data_dir, repo_dir):
        self.repo_dir = repo_dir
        self.data_dir = data_dir
        self.dts_comp_support = int(self.script('dts-comp'))
        self.db = data.DB(data_dir, readonly=True, dtscomp=self.dts_comp_support)
        self.file_cache = {}

    def script(self, *args, input=None):
        return script(*args, input=input, env=self.getEnv())

    def scriptLines(self, *args):
        return scriptLines(*args, env=self.getEnv())

    def getEnv(self):
        return {
            **os.environ,
            "LXR_REPO_DIR": self.repo_dir,
            "LXR_DATA_DIR": self.data_dir,
        }

    def close(self):
        self.db.close()

    def query(self, cmd, *args):
        if cmd == 'versions':

            # Returns the list of indexed versions in the following format:
            # topmenu submenu tag
            # Example: v3 v3.1 v3.1-rc10
            versions = OrderedDict()

            for line in self.scriptLines('list-tags', '-h'):
                taginfo = decode(line).split(' ')
                num = len(taginfo)
                topmenu, submenu = 'FIXME', 'FIXME'

                if num == 1:
                    tag, = taginfo
                elif num == 2:
                    submenu,tag = taginfo
                elif num ==3:
                    topmenu,submenu,tag = taginfo

                if self.db.vers.exists(tag):
                    if topmenu not in versions:
                        versions[topmenu] = OrderedDict()
                    if submenu not in versions[topmenu]:
                        versions[topmenu][submenu] = []
                    versions[topmenu][submenu].append(tag)

            return versions

        elif cmd == 'latest':

            # Returns the latest tag that is included in the database.
            # This excludes release candidates.
            sorted_tags = self.scriptLines('get-latest-tags')

            for tag in sorted_tags:
                if self.db.vers.exists(tag):
                    return tag.decode()

            # return the oldest tag, even if it does not exist in the database
            return sorted_tags[-1].decode()

        elif cmd == 'type':

            # Returns the type (blob or tree) associated to
            # the given path. Example:
            # > ./query.py type v3.1-rc10 /Makefile
            # blob
            # > ./query.py type v3.1-rc10 /arch
            # tree

            version = args[0]
            path = args[1]
            return decode(self.script('get-type', version, path)).strip()

        elif cmd == 'exist':
            version = args[0]
            path = args[1]

            if version not in self.file_cache:
                version_cache = set()
                last_dir = None
                for _, path in self.db.vers.get(version).iter():
                    dirname, filename = os.path.split(path)
                    if dirname != last_dir:
                        last_dir = dirname
                        version_cache.add(dirname)
                    version_cache.add(path)

                self.file_cache[version] = version_cache

            return path.strip('/') in self.file_cache[version]

        elif cmd == 'dir':

            # Returns the contents (trees or blobs) of the specified directory
            # Example: ./query.py dir v3.1-rc10 /arch

            version = args[0]
            path = args[1]
            entries_str =  decode(self.script('get-dir', version, path))
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
                assert family in lib.CACHED_DEFINITIONS_FAMILIES, f"family {family} must have its definitions cached"

                buffer = BytesIO()
                tokens = self.scriptLines('tokenize-file', version, path, family)
                even = True

                prefix = b''
                if family == 'K':
                    prefix = b'CONFIG_'

                for tok in tokens:
                    even = not even
                    tok2 = prefix + tok
                    if even and self.db.defs_cache[family].exists(tok2):
                        tok = b'\033[31m' + tok2 + b'\033[0m'
                    else:
                        tok = lib.unescape(tok)
                    buffer.write(tok)
                return decode(buffer.getvalue())
            else:
                return decode(self.script('get-file', version, path))

        elif cmd == 'family':
            # Get the family of a given file

            filename = args[0]

            return lib.getFileFamily(filename)

        elif cmd == 'dts-comp':
            # Get state of dts_comp_support

            return self.dts_comp_support

        elif cmd == 'dts-comp-exists':
            # Check if a dts compatible string exists

            ident = args[0]
            if self.dts_comp_support:
                return self.db.comps.exists(ident)
            else:
                return False

        elif cmd == 'keys':
            # Return all keys of a given database
            # /!\ This can take a while /!\

            name = args[0]

            if name == 'vars':
                return self.db.vars.get_keys()
            elif name == 'blob':
                return self.db.blob.get_keys()
            elif name == 'hash':
                return self.db.hash.get_keys()
            elif name == 'file':
                return self.db.file.get_keys()
            elif name == 'vers':
                return self.db.vers.get_keys()
            elif name == 'defs':
                return self.db.defs.get_keys()
            elif name == 'refs':
                return self.db.refs.get_keys()
            elif name == 'docs':
                return self.db.docs.get_keys()
            elif name == 'comps' and self.dts_comp_support:
                return self.db.comps.get_keys()
            elif name == 'comps_docs' and self.dts_comp_support:
                return self.db.comps_docs.get_keys()
            else:
                return []

        elif cmd == 'ident':

            # Returns identifier search results

            version = args[0]
            ident = args[1]
            family = args[2]

            # DT bindings compatible strings are handled differently
            if family == 'B':
                defs, refs, docs = self.get_idents_comps(version, ident)
            else:
                defs, refs, docs = self.get_idents_defs(version, ident, family)

            peeks = self.get_peeks_of_syms(version, defs, refs)
            return defs, refs, docs, peeks

        else:
            return 'Unknown subcommand: ' + cmd + '\n'

    def get_file_raw(self, version, path):
        return decode(self.script('get-file', version, path))

    def get_idents_comps(self, version, ident):

        # DT bindings compatible strings are handled differently
        # They are defined in C files
        # Used in DT files
        # Documented in documentation files
        symbol_c = []
        symbol_dts = []
        symbol_docs = []

        # DT compatible strings are quoted in the database
        ident = parse.quote(ident)

        if not self.dts_comp_support or not self.db.comps.exists(ident):
            return symbol_c, symbol_dts, symbol_docs

        files_this_version = self.db.vers.get(version).iter()
        comps = self.db.comps.get(ident).iter(dummy=True)

        if self.db.comps_docs.exists(ident):
            comps_docs = self.db.comps_docs.get(ident).iter(dummy=True)
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

    def get_idents_defs(self, version, ident, family):

        symbol_definitions = []
        symbol_references = []
        symbol_doccomments = []

        if not self.db.defs.exists(ident):
            return symbol_definitions, symbol_references, symbol_doccomments

        if not self.db.vers.exists(version):
            return symbol_definitions, symbol_references, symbol_doccomments

        files_this_version = self.db.vers.get(version).iter()
        this_ident = self.db.defs.get(ident)
        defs_this_ident = this_ident.iter(dummy=True)
        macros_this_ident = this_ident.get_macros()
        # FIXME: see why we can have a discrepancy between defs_this_ident and refs
        if self.db.refs.exists(ident):
            refs = self.db.refs.get(ident).iter(dummy=True)
        else:
            refs = data.RefList().iter(dummy=True)

        if self.db.docs.exists(ident):
            docs = self.db.docs.get(ident).iter(dummy=True)
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

        # Sort dBuf by path name before sorting by type in the loop
        dBuf.sort()

        for path, type, dline in sorted(dBuf, key=lambda d: d[1], reverse=True):
            symbol_definitions.append(SymbolInstance(path, dline, type))

        for path, rlines in sorted(rBuf):
            symbol_references.append(SymbolInstance(path, rlines))

        for path, docline in sorted(docBuf):
            symbol_doccomments.append(SymbolInstance(path, docline))

        return symbol_definitions, symbol_references, symbol_doccomments

    def get_files_and_zip(self, version, syms):
        batch = b"\n".join([f"{version}:{sym.path}".encode() for sym in syms])
        batch_res = self.script('get-files-batch', input=batch)

        # See https://git-scm.com/docs/git-cat-file#_batch_output for the format:
        #
        # <oid> SP <type> SP <size> LF
        # <contents> LF
        # <oid> SP <type> SP <size> LF
        # <contents> LF
        # <oid> SP <type> SP <size> LF
        # <contents> LF
        # 
        for sym in syms:
            meta, batch_res = batch_res.split(b"\n", 1)
            _, _, size = meta.split(b" ")
            size = int(size) + 1 # newline after each file
            content = batch_res[:size].split(b"\n")
            batch_res = batch_res[size:]
            yield sym, content

    def get_peeks_of_syms(self, version, symbol_definitions, symbol_references):
        peeks = {}

        def request_peeks(syms):
            if len(syms) > 100:
                return

            for sym, content in self.get_files_and_zip(version, syms):
                if sym.path not in peeks:
                    peeks[sym.path] = {}

                if type(sym.line) is int:
                    lines = (sym.line,)
                else:
                    lines = map(int, sym.line.split(','))

                for num in lines:
                    index = num - 1
                    if index >= 0 and index < len(content):
                        peeks[sym.path][num] = decode(content[index]).strip()

        request_peeks(symbol_definitions)
        request_peeks(symbol_references)
        return peeks


def cmd_ident(q, version, ident, family, **kwargs):
    symbol_definitions, symbol_references, symbol_doccomments, peeks = q.query("ident", version, ident, family)
    print("Symbol Definitions:")
    for symbol_definition in symbol_definitions:
        print(symbol_definition)

    print("\nSymbol References:")
    for symbol_reference in symbol_references:
        print(symbol_reference)

    print("\nDocumented in:")
    for symbol_doccomment in symbol_doccomments:
        print(symbol_doccomment)

    print("\nSymbol peeks:")
    for file, content in peeks.items():
        for num, line in content.items():
            print(f"{file}:{num}: {line}")

def cmd_file(q, version, path, **kwargs):
    code = q.query("file", version, path)
    print(code)

def profile(q, family, version, ident):
    return q.query('ident', version, ident, family)

def cmd_profile(q, family, version, ident, **kwargs):
    import cProfile
    cProfile.runctx('profile(q, family, version, ident)',
                    globals={
                        "profile": profile
                    },
                    locals={
                        "q": q,
                        "family": family,
                        "version": version,
                        "ident": ident,
                    },
                    sort='tottime'
    )

if __name__ == "__main__":
    import argparse

    query = Query(lib.getDataDir(), lib.getRepoDir())

    parser = argparse.ArgumentParser()
    parser.add_argument("version", help="The version of the project", type=str, default="latest")
    subparsers = parser.add_subparsers()

    ident_subparser = subparsers.add_parser('ident', help="Get definitions and references of an identifier")
    ident_subparser.add_argument('ident', type=str, help="The name of the identifier")
    ident_subparser.add_argument('family', type=str, help="The file family requested")
    ident_subparser.set_defaults(func=cmd_ident, q=query)

    file_subparser = subparsers.add_parser('file', help="Get a source file")
    file_subparser.add_argument('path', type=str, help="The path of the source file")
    file_subparser.set_defaults(func=cmd_file, q=query)

    profile_subparser = subparsers.add_parser('perf', help="Get a source file")
    profile_subparser.add_argument('ident', type=str, help="The name of the identifier")
    profile_subparser.add_argument('family', type=str, help="The file family requested")
    profile_subparser.set_defaults(func=cmd_profile, q=query)

    args = parser.parse_args()
    args.func(**vars(args))
