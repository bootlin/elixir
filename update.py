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

hash_file_lock = Lock() #Lock for db.hash and db.file
defs_lock = Lock() #Lock for db.defs
tag_ready = Condition() #Waiting for new tags

new_idxes = [] # (new idxes, Event idxes ready, Event defs ready)

tags_done = False #True if all tags have been added to new_idxes


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
    def __init__(self):
        Thread.__init__(self, name="UpdateDefsElixir")

    def run(self):
        global new_idxes, tags_done, tag_ready

        self.index = 0

        while(not (tags_done and self.index == len(new_idxes))):
            if(self.index == len(new_idxes)):
                #Wait for new tags
                with tag_ready:
                    tag_ready.wait()
                continue

            new_idxes[self.index][1].wait() #Make sure the tag is ready

            self.update_definitions(new_idxes[self.index][0])

            new_idxes[self.index][2].set() #Tell that UpdateDefs processed the tag

            self.index += 1


    def update_definitions(self, idxes):
        global hash_file_lock, defs_lock

        for idx in idxes:
            if (idx % 1000 == 0): progress('defs: ' + str(idx), self.index+1)

            with hash_file_lock:
                hash = db.hash.get(idx)
                filename = db.file.get(idx)

            family = lib.getFileFamily(filename);
            if family == None: continue

            lines = scriptLines('parse-defs', hash, filename, family)
            for l in lines:
                ident, type, line = l.split(b' ')
                type = type.decode()
                line = int(line.decode())

                with defs_lock:
                    if db.defs.exists(ident):
                        obj = db.defs.get(ident)
                    else:
                        obj = data.DefList()

                obj.add_family(family)
                obj.append(idx, type, line, family)
                if verbose:
                    print(f"def {type} {ident} in #{idx} @ {line}")
                with defs_lock:
                    db.defs.put(ident, obj)


class UpdateRefs(Thread):
    def __init__(self):
        Thread.__init__(self, name="UpdateRefsElixir")

    def run(self):
        global new_idxes, tags_done

        self.index = 0

        while(not (tags_done and self.index == len(new_idxes))):
            if(self.index == len(new_idxes)):
                #Wait for new tags
                with tag_ready:
                    tag_ready.wait()
                continue

            new_idxes[self.index][1].wait() #Make sure the tag is ready
            new_idxes[self.index][2].wait() #Make sure UpdateDefs processed the tag

            self.update_references(new_idxes[self.index][0])

            self.index += 1

    def update_references(self, idxes):
        global hash_file_lock, defs_lock

        for idx in idxes:
            if (idx % 1000 == 0): progress('refs: ' + str(idx), self.index+1)

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
            for tok in tokens:
                even = not even
                if even:
                    tok = prefix + tok

                    with defs_lock:
                        if db.defs.exists(tok) and lib.isIdent(tok):
                            if tok in idents:
                                idents[tok] += ',' + str(line_num)
                            else:
                                idents[tok] = str(line_num)

                else:
                    line_num += tok.count(b'\1')

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
    def __init__(self):
        Thread.__init__(self, name="UpdateDocsElixir")

    def run(self):
        global new_idxes, tags_done

        self.index = 0

        while(not (tags_done and self.index == len(new_idxes))):
            if(self.index == len(new_idxes)):
                #Wait for new tags
                with tag_ready:
                    tag_ready.wait()
                continue

            new_idxes[self.index][1].wait() #Make sure the tag is ready

            self.update_doc_comments(new_idxes[self.index][0])

            self.index += 1

    def update_doc_comments(self, idxes):
        global hash_file_lock

        for idx in idxes:
            if (idx % 1000 == 0): progress('docs: ' + str(idx), self.index+1)

            with hash_file_lock:
                hash = db.hash.get(idx)
                filename = db.file.get(idx)

            family = lib.getFileFamily(filename)
            if family == None: continue

            lines = scriptLines('parse-docs', hash, filename)
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

tag_buf = []
for tag in scriptLines('list-tags'):
    if not db.vers.exists(tag):
        tag_buf.append(tag)

num_tags = len(tag_buf)
project = lib.currentProject()

print(project + ' - found ' + str(len(tag_buf)) + ' new tags')

id_version_thread = UpdateIdVersion(tag_buf)
defs_thread = UpdateDefs()
refs_thread = UpdateRefs()
docs_thread = UpdateDocs()

#Start to process tags
id_version_thread.start()

#Wait until the first tag is ready
with tag_ready:
    tag_ready.wait()

#Start remaining threads
defs_thread.start()
refs_thread.start()
docs_thread.start()

#Make sure all threads finished
id_version_thread.join()
defs_thread.join()
refs_thread.join()
docs_thread.join()
