from concurrent.futures import ProcessPoolExecutor, wait
from multiprocessing import Manager
import logging
from threading import Lock

from elixir.lib import script, scriptLines, getFileFamily, isIdent, getDataDir
from elixir.data import PathList, DefList, RefList, DB, BsdDB

from find_compatible_dts import FindCompatibleDTS

# Holds databases and update changes that are not commited yet
class UpdatePartialState:
    def __init__(self, db, tag, idx_to_hash_and_filename, hash_to_idx):
        self.db = db
        self.tag = tag
        self.idx_to_hash_and_filename = idx_to_hash_and_filename
        self.hash_to_idx = hash_to_idx

        self.defs_lock = Lock()
        self.refs_lock = Lock()
        self.docs_lock = Lock()
        self.comps_lock = Lock()
        self.comps_docs_lock = Lock()

    def get_idx_from_hash(self, hash):
        if hash in self.hash_to_idx:
            return self.hash_to_idx[hash]
        else:
            return self.db.blob.get(hash)

    # Add definitions to database
    def add_defs(self, defs):
        with self.defs_lock:
            for ident, occ_list in defs.items():
                if self.db.defs.exists(ident):
                    obj = self.db.defs.get(ident)
                else:
                    obj = DefList()

                for (idx, type, line, family) in occ_list:
                    obj.append(idx, type, line, family)

                self.db.defs.put(ident, obj)

    # Add references to database
    def add_refs(self, refs):
        with self.refs_lock:
            for ident, idx_to_lines in refs.items():
                obj = self.db.refs.get(ident)
                if obj is None:
                    obj = RefList()

                for (idx, family), lines in idx_to_lines.items():
                    lines_str = ','.join((str(n) for n in lines))
                    obj.append(idx, lines_str, family)

                self.db.refs.put(ident, obj)

    # Add documentation references to database
    def add_docs(self, idx, family, docs):
        with self.docs_lock:
            self.add_to_reflist(self.db.docs, idx, family, docs)

    # Add compatible references to database
    def add_comps(self, idx, family, comps):
        with self.comps_lock:
            self.add_to_reflist(self.db.comps, idx, family, comps)

    # Add compatible docs to database
    def add_comps_docs(self, idx, family, comps_docs):
        with self.comps_docs_lock:
            self.add_to_reflist(self.db.comps_docs, idx, family, comps_docs)

    # Add data to database file that uses reflist schema
    def add_to_reflist(self, db_file, idx, family, to_add):
        for ident, lines in to_add.items():
            if db_file.exists(ident):
                obj = db_file.get(ident)
            else:
                obj = RefList()

            lines_str = ','.join((str(n) for n in lines))
            obj.append(idx, lines_str, family)
            db_file.put(ident, obj)


# NOTE: not thread safe, has to be ran before the actual job is started
# Builds UpdatePartialState
def build_partial_state(db, tag):
    if db.vars.exists('numBlobs'):
        idx = db.vars.get('numBlobs')
    else:
        idx = 0

    # Get blob hashes and associated file names (without path)
    blobs = scriptLines('list-blobs', '-f', tag)

    idx_to_hash_and_filename = {}
    hash_to_idx = {}

    # Collect new blobs, assign database ids to the blobs
    for blob in blobs:
        hash, filename = blob.split(b' ',maxsplit=1)
        blob_exist = db.blob.exists(hash)
        if not blob_exist:
            hash_to_idx[hash] = idx
            idx_to_hash_and_filename[idx] = (hash, filename.decode())
            idx += 1

    # reserve ids in blob space.
    # NOTE: this variable does not represent the actual number of blos in the database now,
    # just the number of ids reserved for blobs. the space is not guaranteed to be continous
    # if update job is interrupted or versions are scrubbed from the database.
    db.vars.put('numBlobs', idx)

    return UpdatePartialState(db, tag, idx_to_hash_and_filename, hash_to_idx)

# NOTE: not thread safe, has to be ran after job is finished
# Applies changes from partial update state - mainly to hash, file, blob and versions databases
# It is assumed that indexes not present in versions are ignored
def apply_partial_state(state: UpdatePartialState):
    for idx, (hash, filename) in state.idx_to_hash_and_filename.items():
        state.db.hash.put(idx, hash)
        state.db.file.put(idx, filename)

    for hash, idx in state.hash_to_idx.items():
        state.db.blob.put(hash, idx)

    # Update versions
    blobs = scriptLines('list-blobs', '-p', state.tag)
    buf = []

    for blob in blobs:
        hash, path = blob.split(b' ', maxsplit=1)
        idx = state.get_idx_from_hash(hash)
        buf.append((idx, path))

    buf.sort()
    obj = PathList()
    for idx, path in buf:
        obj.append(idx, path)

    state.db.vers.put(state.tag, obj, sync=True)


# Get definitions for a file
def get_defs(idx, hash, filename, defs):
    family = getFileFamily(filename)
    if family in [None, 'M']:
        return

    lines = scriptLines('parse-defs', hash, filename, family)

    for l in lines:
        ident, type, line = l.split(b' ')
        type = type.decode()
        line = int(line.decode())
        if isIdent(ident):
            if ident not in defs:
                defs[ident] = []
            defs[ident].append((idx, type, line, family))

    return defs


# NOTE: it is assumed that update_refs and update_defs are not running
# concurrently. hence, defs are not locked
# defs database MUSNT be updated while get_refs is running
# Get references for a file
def get_refs(idx, hash, filename, defs, refs):
    family = getFileFamily(filename)
    if family is None:
        return

    # Kconfig values are saved as CONFIG_<value>
    prefix = b'' if family != 'K' else b'CONFIG_'

    tokens = scriptLines('tokenize-file', '-b', hash, family)
    even = True
    line_num = 1

    for tok in tokens:
        even = not even
        if even:
            tok = prefix + tok
            deflist = defs.get(tok)

            if deflist and not deflist.exists(str(idx).encode(), line_num):
                # We only index CONFIG_??? in makefiles
                if (family != 'M' or tok.startswith(b'CONFIG_')):
                    if tok not in refs:
                        refs[tok] = {}

                    if (idx, family) not in refs[tok]:
                        refs[tok][(idx, family)] = []

                    refs[tok][(idx, family)].append(line_num)

        else:
            line_num += tok.count(b'\1')

    return refs

# Collect compatible script output into reflist-schema compatible format
def collect_get_blob_output(lines):
    results = {}
    for l in lines:
        ident, line = l.split(' ')
        line = int(line)

        if ident not in results:
            results[ident] = []
        results[ident].append(line)

    return results

# Get docs for a single file
def get_docs(idx, hash, filename):
    family = getFileFamily(filename)
    if family in [None, 'M']: return

    lines = (line.decode() for line in scriptLines('parse-docs', hash, filename))
    docs = collect_get_blob_output(lines)

    return (idx, family, docs)

# Get compatible references for a single file
def get_comps(idx, hash, filename):
    family = getFileFamily(filename)
    if family in [None, 'K', 'M']: return

    compatibles_parser = FindCompatibleDTS()
    lines = compatibles_parser.run(scriptLines('get-blob', hash), family)
    comps = collect_get_blob_output(lines)

    return (idx, family, comps)

# Get compatible documentation references for a single file
# NOTE: assumes comps is not running concurrently
def get_comps_docs(idx, hash, _, comps):
    family = 'B'

    compatibles_parser = FindCompatibleDTS()
    lines = compatibles_parser.run(scriptLines('get-blob', hash), family)
    comps_docs = {}
    for l in lines:
        ident, line = l.split(' ')

        if comps.exists(ident):
            if ident not in comps_docs:
                comps_docs[ident] = []
            comps_docs[ident].append(int(line))

    return (idx, family, comps_docs)

def batch(job):
    def f(chunk, **kwargs):
        return [job(*args, **kwargs) for args in chunk]
    return f

# NOTE: some of the following functions are kind of redundant, and could sometimes be
# higher-order functions, but that's not supported by multiprocessing

def batch_defs(chunk):
    defs = {}
    for ch in chunk:
        get_defs(*ch, defs=defs)
    return defs

# Handle defs task results
def handle_defs_results(state):
    def f(future):
        try:
            result = future.result()
            if result is not None:
                state.add_defs(result)
        except Exception:
            logging.exception(f"handling future results for defs raised")
    return f

def batch_docs(*args, **kwargs): return batch(get_docs)(*args, **kwargs)
def batch_comps(*args, **kwargs): return batch(get_comps)(*args, **kwargs)

# Run references tasks on a chunk
# NOTE: references can open definitions database in read-only mode, because
# definitions job was finished
def batch_refs(chunk, **kwargs):
    defs = BsdDB(getDataDir() + '/definitions.db', True, DefList)
    refs = {}
    for args in chunk:
        get_refs(*args, defs=defs, refs=refs, **kwargs)
    defs.close()
    return refs

# Handle refs task results
def handle_refs_results(state):
    def f(future):
        try:
            result = future.result()
            if result is not None:
                state.add_refs(result)
        except Exception:
            logging.exception(f"handling future results for refs raised")
    return f

# Run comps_docs tasks on a chunk
# NOTE: compatibledts database can be opened for the same reasons as in batch_refs
def batch_comps_docs(chunk, **kwargs):
    comps = BsdDB(getDataDir() + '/compatibledts.db', True, DefList)
    result = [get_comps_docs(*args, comps=comps, **kwargs) for args in chunk]
    comps.close()
    return result

def handle_batch_results(callback):
    def f(future):
        try:
            results = future.result()
            for result in results:
                if result is not None:
                    callback(*result)
        except Exception:
            logging.exception(f"handling future results for {callback.__name__} raised")
    return f

# Split list into sublist of chunk_size size
def split_into_chunks(list, chunk_size):
    return [list[i:i+chunk_size] for i in range(0, len(list), chunk_size)]

# Update a single version
def update_version(db, tag, pool, manager, chunk_size, dts_comp_support):
    state = build_partial_state(db, tag)

    # Collect blobs to process and split list of blobs into chunks
    idxes = [(idx, hash, filename) for (idx, (hash, filename)) in state.idx_to_hash_and_filename.items()]
    chunks = split_into_chunks(idxes, chunk_size)

    def after_all_defs_done():
        # NOTE: defs database cannot be written to from now on. This is very important - process pool is used,
        # and bsddb cannot be shared between processes until/unless bsddb concurrent data store is implemented.
        # Operations on closed databases raise exceptions that would in this case be indicative of a bug.
        state.db.defs.sync()
        state.db.defs.close()
        print("defs db closed")

        # Start refs job
        futures = [pool.submit(batch_refs, ch) for ch in chunks]
        return ("refs", (futures, handle_refs_results(state), None))

    def after_all_comps_done():
        state.db.comps.sync()
        state.db.comps.close()
        print("comps db closed")

        # Start comps_docs job
        futures = [pool.submit(batch_comps_docs, ch) for ch in chunks]
        return ("comps_docs", (futures, handle_batch_results(state.add_comps_docs), None))

    # Used to track futures for jobs, what to do after a single future finishes,
    # and after the whole job finishes
    to_track = {
        "defs": ([], handle_defs_results(state), after_all_defs_done),
        "docs": ([], handle_batch_results(state.add_docs), None),
    }

    if dts_comp_support:
        to_track["comps"] = ([], handle_batch_results(state.add_comps), after_all_comps_done)

    # Start initial jobs for all chunks
    for ch in chunks:
        to_track["defs"][0].append(pool.submit(batch_defs, ch))
        to_track["docs"][0].append(pool.submit(batch_docs, ch))

        if dts_comp_support:
            to_track["comps"][0].append(pool.submit(batch_comps, ch))


    # Used to track progress of jobs
    total_lengths = {
        k: (0, len(v[0])) for k, v in to_track.items()
    }

    # track job progress
    while len(to_track) != 0:
        new_to_track = {}

        for name, (futures, after_single_done, after_all_done) in to_track.items():
            new_futures = futures

            if len(futures) != 0:
                result = wait(futures, timeout=1)

                if len(result.done) != 0:
                    total_lengths[name] = (total_lengths[name][0] + len(result.done), total_lengths[name][1])
                    print(name, f"progress: {int((total_lengths[name][0]/total_lengths[name][1])*100)}%")
                    new_futures = [f for f in futures if f not in result.done]

                    for f in result.done:
                        if after_single_done is not None:
                            after_single_done(f)

                if len(new_futures) == 0:
                    if after_all_done is not None:
                        k, v = after_all_done()
                        new_to_track[k] = v
                        total_lengths[k] = (0, len(v[0]))
                else:
                    new_to_track[name] = (new_futures, after_single_done, after_all_done)
            else:
                new_to_track[name] = (new_futures, after_single_done, after_all_done)

        to_track = new_to_track

    print("update done, applying partial state")
    apply_partial_state(state)

if __name__ == "__main__":
    dts_comp_support = int(script('dts-comp'))
    db = None

    manager = Manager()
    with ProcessPoolExecutor() as pool:
        for tag in scriptLines('list-tags'):
            if db is None:
                db = DB(getDataDir(), readonly=False, dtscomp=dts_comp_support, shared=True)

            if not db.vers.exists(tag):
                print("updating tag", tag)
                update_version(db, tag, pool, manager, 1000, dts_comp_support)
                db.close()
                db = None

