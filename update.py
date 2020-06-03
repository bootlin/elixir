#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017--2020 Mikaël Bouillot <mikael.bouillot@bootlin.com>
#                           Maxime Chretien <maxime.chretien@bootlin.com>
#                           and contributors
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
from threading import Thread, Lock, Event, Condition

verbose = False

db = data.DB(lib.getDataDir(), readonly=False)

#Number of cpu threads (+1 for version indexing)
cpu = 8
threads_list = []

hash_file_lock = Lock() #Lock for db.hash and db.file
defs_lock = Lock() #Lock for db.defs
refs_lock = Lock() #Lock for db.refs
docs_lock = Lock() #Lock for db.docs
tag_ready = Condition() #Waiting for new tags

new_idxes = [] # (new idxes, Event idxes ready, Event defs ready)

tags_done = False #True if all tags have been added to new_idxes

#Progress variables
tags_defs = 0
tags_defs_lock = Lock()
tags_refs = 0
tags_refs_lock = Lock()
tags_docs = 0
tags_docs_lock = Lock()

class UpdateIdVersion(Thread):
    def __init__(self, tag_buf):
        Thread.__init__(self, name="UpdateIdVersionElixir")
        self.tag_buf = tag_buf

    def run(self):
        global new_idxes, tags_done, tag_ready
        self.index = 0

        for tag in self.tag_buf:

            new_idxes.append((self.update_blob_ids(tag), Event(), Event()))

            progress(tag.decode() + ': ' + str(len(new_idxes[self.index][0])) +
                        ' new blobs', self.index+1)

            self.update_versions(tag)

            new_idxes[self.index][1].set() #Tell that the tag is ready

            self.index += 1

            #Wake up waiting threads
            with tag_ready:
                tag_ready.notify_all()

        tags_done = True

    def update_blob_ids(self, tag):

        global hash_file_lock

        if db.vars.exists('numBlobs'):
            idx = db.vars.get('numBlobs')
        else:
            idx = 0

        # Get blob hashes and associated file names (without path)
        blobs = scriptLines('list-blobs', '-f', tag)

        new_idxes = []
        for blob in blobs:
            hash, filename = blob.split(b' ',maxsplit=1)
            if not db.blob.exists(hash):
                db.blob.put(hash, idx)

                with hash_file_lock:
                    db.hash.put(idx, hash)
                    db.file.put(idx, filename)

                new_idxes.append(idx)
                if verbose:
                    print(f"New blob #{idx} {hash}:{filename}")
                idx += 1
        db.vars.put('numBlobs', idx)
        return new_idxes

    def update_versions(self, tag):

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


class UpdateDefs(Thread):
    def __init__(self, start, inc):
        Thread.__init__(self, name="UpdateDefsElixir")
        self.index = start
        self.inc = inc # Equivalient to the number of defs threads

    def run(self):
        global new_idxes, tags_done, tag_ready, tags_defs, tags_defs_lock

        while(not (tags_done and self.index >= len(new_idxes))):
            if(self.index >= len(new_idxes)):
                # Wait for new tags
                with tag_ready:
                    tag_ready.wait()
                continue

            new_idxes[self.index][1].wait() # Make sure the tag is ready

            with tags_defs_lock:
                tags_defs += 1

            self.update_definitions(new_idxes[self.index][0])

            new_idxes[self.index][2].set() # Tell that UpdateDefs processed the tag

            self.index += self.inc


    def update_definitions(self, idxes):
        global hash_file_lock, defs_lock, tags_defs

        for idx in idxes:
            if (idx % 1000 == 0): progress('defs: ' + str(idx), tags_defs)

            with hash_file_lock:
                hash = db.hash.get(idx)
                filename = db.file.get(idx)

            family = lib.getFileFamily(filename);
            if family == None: continue

            lines = scriptLines('parse-defs', hash, filename, family)

            with defs_lock:
                for l in lines:
                    ident, type, line = l.split(b' ')
                    type = type.decode()
                    line = int(line.decode())

                    if db.defs.exists(ident):
                        obj = db.defs.get(ident)
                    else:
                        obj = data.DefList()

                    obj.add_family(family)
                    obj.append(idx, type, line, family)
                    if verbose:
                        print(f"def {type} {ident} in #{idx} @ {line}")
                    db.defs.put(ident, obj)


class UpdateRefs(Thread):
    def __init__(self, start, inc):
        Thread.__init__(self, name="UpdateRefsElixir")
        self.index = start
        self.inc = inc # Equivalient to the number of refs threads

    def run(self):
        global new_idxes, tags_done, tags_refs, tags_refs_lock

        while(not (tags_done and self.index >= len(new_idxes))):
            if(self.index >= len(new_idxes)):
                # Wait for new tags
                with tag_ready:
                    tag_ready.wait()
                continue

            new_idxes[self.index][1].wait() # Make sure the tag is ready
            new_idxes[self.index][2].wait() # Make sure UpdateDefs processed the tag

            with tags_refs_lock:
                tags_refs += 1

            self.update_references(new_idxes[self.index][0])

            self.index += self.inc

    def update_references(self, idxes):
        global hash_file_lock, defs_lock, refs_lock, tags_refs

        for idx in idxes:
            if (idx % 1000 == 0): progress('refs: ' + str(idx), tags_refs)

            with hash_file_lock:
                hash = db.hash.get(idx)
                filename = db.file.get(idx)

            family = lib.getFileFamily(filename)
            if family == None: continue

            prefix = b''
            # Kconfig values are saved as CONFIG_<value>
            if family == 'K':
                prefix = b'CONFIG_'

            tokens = scriptLines('tokenize-file', '-b', hash, family)
            even = True
            line_num = 1
            idents = {}
            with defs_lock:
                for tok in tokens:
                    even = not even
                    if even:
                        tok = prefix + tok

                        if db.defs.exists(tok) and lib.isIdent(tok):
                            if tok in idents:
                                idents[tok] += ',' + str(line_num)
                            else:
                                idents[tok] = str(line_num)

                    else:
                        line_num += tok.count(b'\1')

            with refs_lock:
                for ident, lines in idents.items():
                    if db.refs.exists(ident):
                        obj = db.refs.get(ident)
                    else:
                        obj = data.RefList()

                    obj.append(idx, lines, family)
                    if verbose:
                        print(f"ref: {ident} in #{idx} @ {lines}")
                    db.refs.put(ident, obj)


class UpdateDocs(Thread):
    def __init__(self, start, inc):
        Thread.__init__(self, name="UpdateDocsElixir")
        self.index = start
        self.inc = inc # Equivalient to the number of docs threads

    def run(self):
        global new_idxes, tags_done, tags_docs, tags_docs_lock

        while(not (tags_done and self.index >= len(new_idxes))):
            if(self.index >= len(new_idxes)):
                # Wait for new tags
                with tag_ready:
                    tag_ready.wait()
                continue

            new_idxes[self.index][1].wait() # Make sure the tag is ready

            with tags_docs_lock:
                tags_docs += 1

            self.update_doc_comments(new_idxes[self.index][0])

            self.index += self.inc

    def update_doc_comments(self, idxes):
        global hash_file_lock, docs_lock, tags_docs

        for idx in idxes:
            if (idx % 1000 == 0): progress('docs: ' + str(idx), tags_docs)

            with hash_file_lock:
                hash = db.hash.get(idx)
                filename = db.file.get(idx)

            family = lib.getFileFamily(filename)
            if family == None: continue

            lines = scriptLines('parse-docs', hash, filename)
            with docs_lock:
                for l in lines:
                    ident, line = l.split(b' ')
                    line = int(line.decode())

                    if db.docs.exists(ident):
                        obj = db.docs.get(ident)
                    else:
                        obj = data.RefList()

                    obj.append(idx, str(line), family)
                    if verbose:
                        print(f"doc: {ident} in #{idx} @ {line}")
                    db.docs.put(ident, obj)


def progress(msg, current):
    print('{} - {} ({:.0%})'.format(project, msg, current/num_tags))


# Main

# Check number of threads arg
if len(argv) >= 2 and argv[1].isdigit() :
    cpu = int(argv[1])

    if cpu < 3 :
        cpu = 3

# Distribute threads among functions using the following rules :
# There are more refs threads than others
# There are more (or equal) defs threads than docs threads
# Example : if cpu=6 : refs=3, defs=2, docs=1
#           if cpu=7 : refs=3, defs=2, docs=2
#           if cpu=8 : refs=4, defs=2, docs=2
#           if cpu=11: refs=5, defs=3, docs=3
quo, rem = divmod(cpu, 2)
num_th_refs = quo

quo, rem = divmod(quo+rem, 2)
num_th_defs = quo + rem
num_th_docs = quo


tag_buf = []
for tag in scriptLines('list-tags'):
    if not db.vers.exists(tag):
        tag_buf.append(tag)

num_tags = len(tag_buf)
project = lib.currentProject()

print(project + ' - found ' + str(len(tag_buf)) + ' new tags')

id_version_thread = UpdateIdVersion(tag_buf)

# Define defs threads
for i in range(num_th_defs):
    threads_list.append(UpdateDefs(i, num_th_defs))
# Define refs threads
for i in range(num_th_refs):
    threads_list.append(UpdateRefs(i, num_th_refs))
# Define docs threads
for i in range(num_th_docs):
    threads_list.append(UpdateDocs(i, num_th_docs))

# Start to process tags
id_version_thread.start()

# Wait until the first tag is ready
with tag_ready:
    tag_ready.wait()

# Start remaining threads
for i in range(len(threads_list)):
    threads_list[i].start()

# Make sure all threads finished
id_version_thread.join()
for i in range(len(threads_list)):
    threads_list[i].join()
