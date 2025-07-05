import os.path
import logging
import time
from multiprocessing import cpu_count, set_start_method
from multiprocessing.pool import Pool
from typing import Dict, Iterable, List, Optional, Tuple, Set

from find_compatible_dts import FindCompatibleDTS

from elixir.data import DB, BsdDB, DefList, PathList, RefList
from elixir.lib import (
    compatibleFamily,
    compatibleMacro,
    getDataDir,
    getFileFamily,
    isIdent,
    script,
    scriptLines,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# File identification - id, hash, filename
FileId = Tuple[int, bytes, str]

# Definitions parsing output, ident -> list of (file_idx, type, line, family)
DefsDict = Dict[bytes, List[Tuple[int, str, int, str]]]

# References parsing output, ident -> (file_idx, family) -> list of lines
RefsDict = Dict[bytes, Dict[Tuple[int, str], List[int]]]

# Generic dictionary of ident -> list of lines
LinesListDict = Dict[str, List[int]]

# File idx -> (hash, filename, is a new file?)
IdxCache = Dict[int, Tuple[bytes, str, bool]]

# Check if definition for ident is visible in current version
def def_in_version(db: DB, idx_to_hash_and_filename: IdxCache, ident: bytes) -> bool:
    defs_this_ident = db.defs.get(ident)
    if not defs_this_ident:
        return False

    for def_idx, _, _, _ in defs_this_ident.iter():
        if def_idx in idx_to_hash_and_filename:
            return True

    return False

# Add definitions to database
def add_defs(db: DB, defs: DefsDict):
    for ident, occ_list in defs.items():
        obj = db.defs.get(ident)
        if obj is None:
            obj = DefList()

        for (idx, type, line, family) in occ_list:
            obj.append(idx, type, line, family)

        db.defs.put(ident, obj)

# Add references to database
def add_refs(db: DB, idx_to_hash_and_filename: IdxCache, refs: RefsDict):
    for ident, idx_to_lines in refs.items():
        deflist = db.defs.get(ident)
        if deflist is None:
            continue

        in_version = def_in_version(db, idx_to_hash_and_filename, ident)
        if not in_version:
            continue

        def deflist_exists(idx: int, line: int):
            for def_idx, _, def_line, _ in deflist.iter():
                if def_idx == idx and def_line == line:
                    return True
            return False

        obj = db.refs.get(ident)
        if obj is None:
            obj = RefList()

        modified = False
        for (idx, family), lines in idx_to_lines.items():
            lines = [n for n in lines if not deflist_exists(idx, n)]

            if len(lines) != 0:
                lines_str = ','.join((str(n) for n in lines))
                obj.append(idx, lines_str, family)
                modified = True

        if modified:
            db.refs.put(ident, obj)

# Add documentation references to database
def add_docs(db: DB, idx: int, family: str, docs: Dict[str, List[int]]):
    add_to_lineslist(db.docs, idx, family, docs)

# Add compatible references to database
def add_comps(db: DB, idx: int, family: str, comps: Dict[str, List[int]]):
    add_to_lineslist(db.comps, idx, family, comps)

# Add compatible docs to database
def add_comps_docs(db: DB, idx: int, family: str, comps_docs: Dict[str, List[int]]):
    comps_result = {}
    for ident, v in comps_docs.items():
        if db.comps.exists(ident):
            comps_result[ident] = v

    add_to_lineslist(db.comps_docs, idx, family, comps_result)

# Add data to a database file that uses lines list schema
def add_to_lineslist(db_file: BsdDB, idx: int, family: str, to_add: Dict[str, List[int]]):
    for ident, lines in to_add.items():
        obj = db_file.get(ident)
        if obj is None:
            obj = RefList()

        lines_str = ','.join((str(n) for n in lines))
        obj.append(idx, lines_str, family)
        db_file.put(ident, obj)


# Adds blob list to database, returns blob id -> (hash, filename) dict
def collect_blobs(db: DB, tag: bytes) -> IdxCache:
    idx = db.vars.get('numBlobs')
    if idx is None:
        idx = 0

    # Get blob hashes and associated file names (without path)
    blobs = scriptLines('list-blobs', '-p', tag)
    versionBuf = []
    idx_to_hash_and_filename = {}

    # Collect new blobs, assign database ids to the blobs
    for blob in blobs:
        hash, path = blob.split(b' ',maxsplit=1)
        filename = os.path.basename(path.decode())
        blob_idx = db.blob.get(hash)

        if blob_idx is not None:
            versionBuf.append((blob_idx, path))
            if blob_idx not in idx_to_hash_and_filename:
                idx_to_hash_and_filename[blob_idx] = (hash, filename, False)
        else:
            versionBuf.append((idx, path))
            idx_to_hash_and_filename[idx] = (hash, filename, True)
            db.blob.put(hash, idx)
            db.hash.put(idx, hash)
            db.file.put(idx, filename)
            idx += 1

    # Update number of blobs in the database
    db.vars.put('numBlobs', idx)

    # Add mapping blob id -> path to version database
    versionBuf.sort()
    obj = PathList()
    for i, path in versionBuf:
        obj.append(i, path)
    db.vers.put(tag, obj, sync=True)

    return idx_to_hash_and_filename

# Generate definitions cache databases
def generate_defs_caches(db: DB):
    for key in db.defs.get_keys():
        value = db.defs.get(key)
        for family in ['C', 'K', 'D', 'M']:
            if (compatibleFamily(value.get_families(), family) or
                        compatibleMacro(value.get_macros(), family)):
                db.defs_cache[family].put(key, b'')


# Collect definitions from ctags for a file
def get_defs(file_id: FileId) -> Optional[DefsDict]:
    idx, hash, filename = file_id
    defs = {}
    family = getFileFamily(filename)
    if family in (None, 'M'):
        return None

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

# Collect references from the tokenizer for a file
def get_refs(file_id: FileId) -> Optional[RefsDict]:
    idx, hash, filename = file_id
    refs = {}
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

# Collect compatible script output into lineslinst-schema compatible format
def collect_get_blob_output(lines: Iterable[str]) -> LinesListDict:
    results = {}
    for l in lines:
        ident, line = l.split(' ')
        line = int(line)

        if ident not in results:
            results[ident] = []
        results[ident].append(line)

    return results

# Collect docs from doc comments script for a single file
def get_docs(file_id: FileId) -> Optional[Tuple[int, str, LinesListDict]]:
    idx, hash, filename = file_id
    family = getFileFamily(filename)
    if family in (None, 'M'): return

    start = time.time()
    lines = (line.decode() for line in scriptLines('parse-docs', hash, filename))
    parser_time = time.time()-start

    if parser_time > 10:
        print("docs timeout", parser_time, file_id)

    docs = collect_get_blob_output(lines)

    return (idx, family, docs)

# Collect compatible references for a single file
def get_comps(file_id: FileId) -> Optional[Tuple[int, str, LinesListDict]]:
    idx, hash, filename = file_id
    family = getFileFamily(filename)
    if family in (None, 'K', 'M'): return

    compatibles_parser = FindCompatibleDTS()

    start = time.time()
    lines = compatibles_parser.run(scriptLines('get-blob', hash), family)
    parser_time = time.time()-start

    if parser_time > 10:
        print("comps docs timeout", parser_time, file_id)

    comps = collect_get_blob_output(lines)

    return (idx, family, comps)

# Collect compatible documentation references for a single file
def get_comps_docs(file_id: FileId) -> Optional[Tuple[int, str, LinesListDict]]:
    idx, hash, _ = file_id
    family = 'B'

    compatibles_parser = FindCompatibleDTS()
    lines = compatibles_parser.run(scriptLines('get-blob', hash), family)
    comps_docs = {}
    for l in lines:
        ident, line = l.split(' ')

        if ident not in comps_docs:
            comps_docs[ident] = []
        comps_docs[ident].append(int(line))

    return (idx, family, comps_docs)


# Update a single version - collects data from all the stages and saves it in the database
def update_version(db: DB, tag: bytes, pool: Pool, dts_comp_support: bool):
    idx_to_hash_and_filename = collect_blobs(db, tag)

    # Collect blobs to process and split list of blobs into chunks
    idxes = [(idx, hash, filename) for (idx, (hash, filename, new)) in idx_to_hash_and_filename.items() if new]
    chunksize = int(len(idxes) / cpu_count())
    chunksize = min(max(1, chunksize), 100)

    logger.info("collecting blobs done")

    for result in pool.imap_unordered(get_defs, idxes, chunksize):
        if result is not None:
            add_defs(db, result)

    logger.info("defs done")

    for result in pool.imap_unordered(get_docs, idxes, chunksize):
        if result is not None:
            add_docs(db, *result)

    logger.info("docs done")

    if dts_comp_support:
        comp_idxes = [idx for idx in idxes if getFileFamily(idx[2]) not in (None, 'K', 'M')]
        comp_chunksize = int(len(comp_idxes) / cpu_count())
        comp_chunksize = min(max(1, comp_chunksize), 100)
        for result in pool.imap_unordered(get_comps, comp_idxes, comp_chunksize):
            if result is not None:
                add_comps(db, *result)

        logger.info("dts comps done")

        for result in pool.imap_unordered(get_comps_docs, idxes, chunksize):
            if result is not None:
                add_comps_docs(db, *result)

        logger.info("dts comps docs done")

    ref_idxes = [idx for idx in idxes if getFileFamily(idx[2]) is not None]
    ref_chunksize = int(len(ref_idxes) / cpu_count())
    ref_chunksize = min(max(1, ref_chunksize), 100)
    for result in pool.imap_unordered(get_refs, ref_idxes, ref_chunksize):
        if result is not None:
            add_refs(db, idx_to_hash_and_filename, result)

    logger.info("refs done")
    logger.info("update done")

if __name__ == "__main__":
    dts_comp_support = bool(int(script('dts-comp')))
    db = DB(getDataDir(), readonly=False, dtscomp=dts_comp_support, shared=False, update_cache=100000)

    set_start_method('spawn')
    with Pool() as pool:
        for tag in scriptLines('list-tags'):
            if not tag.startswith(b'v6.1') or b'rc' in tag:
                continue

            if not db.vers.exists(tag):
                logger.info("updating tag %s", tag)
                update_version(db, tag, pool, dts_comp_support)

    generate_defs_caches(db)
    db.close()

