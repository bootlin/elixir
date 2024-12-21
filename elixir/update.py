import logging
from multiprocessing import cpu_count
from multiprocessing.pool import Pool
from typing import Dict, Iterable, List, Optional, Tuple

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

# Cache of definitions found in current tag, ident -> list of (file_idx, line)
DefCache = Dict[bytes, List[Tuple[int, int]]]

# Generic dictionary of ident -> list of lines
LinesListDict = Dict[str, List[int]]

# Add definitions to database
def add_defs(db: DB, def_cache: DefCache, defs: DefsDict):
    for ident, occ_list in defs.items():
        obj = db.defs.get(ident)
        if obj is None:
            obj = DefList()

        if ident in def_cache:
            lines_list = def_cache[ident]
        else:
            lines_list = []
            def_cache[ident] = lines_list

        for (idx, type, line, family) in occ_list:
            obj.append(idx, type, line, family)
            lines_list.append((idx, line))

        db.defs.put(ident, obj)

# Add references to database
def add_refs(db: DB, def_cache: DefCache, refs: RefsDict):
    for ident, idx_to_lines in refs.items():
        # Skip reference if definition was not collected in this tag
        deflist = def_cache.get(ident)
        if deflist is None:
            continue

        def deflist_exists(idx, n):
            for didx, dn in deflist:
                if didx == idx and dn == n:
                    return True
            return False

        obj = db.refs.get(ident)
        if obj is None:
            obj = RefList()

        for (idx, family), lines in idx_to_lines.items():
            lines = [n for n in lines if not deflist_exists(str(idx).encode(), n)]

            if len(lines) != 0:
                lines_str = ','.join((str(n) for n in lines))
                obj.append(idx, lines_str, family)

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
def collect_blobs(db: DB, tag: bytes) -> Dict[int, Tuple[bytes, str]]:
    idx = db.vars.get('numBlobs')
    if idx is None:
        idx = 0

    # Get blob hashes and associated file names (without path)
    blobs = scriptLines('list-blobs', '-f', tag)
    versionBuf = []
    idx_to_hash_and_filename = {}

    # Collect new blobs, assign database ids to the blobs
    for blob in blobs:
        hash, filename = blob.split(b' ',maxsplit=1)
        blob_exist = db.blob.exists(hash)
        versionBuf.append((idx, filename))
        if not blob_exist:
            idx_to_hash_and_filename[idx] = (hash, filename.decode())
            db.blob.put(hash, idx)
            db.hash.put(idx, hash)
            db.file.put(idx, filename)
            idx += 1

    # Update number of blobs in the database
    db.vars.put('numBlobs', idx)

    # Add mapping blob id -> path to version database
    versionBuf.sort()
    obj = PathList()
    for idx, path in versionBuf:
        obj.append(idx, path)
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

    lines = (line.decode() for line in scriptLines('parse-docs', hash, filename))
    docs = collect_get_blob_output(lines)

    return (idx, family, docs)

# Collect compatible references for a single file
def get_comps(file_id: FileId) -> Optional[Tuple[int, str, LinesListDict]]:
    idx, hash, filename = file_id
    family = getFileFamily(filename)
    if family in (None, 'K', 'M'): return

    compatibles_parser = FindCompatibleDTS()
    lines = compatibles_parser.run(scriptLines('get-blob', hash), family)
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
    def_cache = {}

    # Collect blobs to process and split list of blobs into chunks
    idxes = [(idx, hash, filename) for (idx, (hash, filename)) in idx_to_hash_and_filename.items()]
    chunksize = int(len(idxes) / cpu_count())
    chunksize = min(max(1, chunksize), 100)

    collect_blobs(db, tag)
    logger.info("collecting blobs done")

    for result in pool.imap_unordered(get_defs, idxes, chunksize):
        if result is not None:
            add_defs(db, def_cache, result)

    logger.info("defs done")

    for result in pool.imap_unordered(get_docs, idxes, chunksize):
        if result is not None:
            add_docs(db, *result)

    logger.info("docs done")

    if dts_comp_support:
        for result in pool.imap_unordered(get_comps, idxes, chunksize):
            if result is not None:
                add_comps(db, *result)

        logger.info("dts comps done")

        for result in pool.imap_unordered(get_comps_docs, idxes, chunksize):
            if result is not None:
                add_comps_docs(db, *result)

        logger.info("dts comps docs done")

    for result in pool.imap_unordered(get_refs, idxes, chunksize):
        if result is not None:
            add_refs(db, def_cache, result)

    logger.info("refs done")

    generate_defs_caches(db)
    logger.info("update done")


if __name__ == "__main__":
    dts_comp_support = bool(int(script('dts-comp')))
    db = None

    with Pool() as pool:
        for tag in scriptLines('list-tags'):
            if db is None:
                db = DB(getDataDir(), readonly=False, dtscomp=dts_comp_support, shared=False, update_cache=True)

            if not db.vers.exists(tag):
                logger.info("updating tag %s", tag)
                update_version(db, tag, pool, dts_comp_support)
                db.close()
                db = None

