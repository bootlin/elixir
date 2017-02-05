#!/usr/bin/python3

from sys import argv
from lib import echo, script, scriptLines
import lib

db = lib.DB()

cmd = argv[1]

if cmd == 'versions':
    p = script ('list-tags')
    echo (p)

elif cmd == 'dir':
    version = argv[2]
    path = argv[3]
    p = script ('get-dir', version, path)
    echo (p)

elif cmd == 'file':
    version = argv[2]
    path = argv[3]
    ext = path[-2:]

    if ext == '.c' or ext == '.h':
        tokens = scriptLines ('tokenize-file', version, path)
        toBe = True
        for tok in tokens:
            toBe = not toBe
            if toBe and db.defs.exists (tok) and lib.isIdent (tok):
                tok = b'\033[31m' + tok + b'\033[0m'
            else:
                tok = lib.unescape (tok)
            echo (tok)
    else:
        p = script ('get-file', version, path)
        echo (p)

elif cmd == 'ident':
    version = argv[2]
    ident = argv[3]

    if not db.defs.exists (ident):
        print (argv[0] + ': Unknown identifier: ' + ident)
        exit()

    vers = db.vers.get (version).iter()
    defs = db.defs.get (ident).iter()
    refs = db.refs.get (ident).iter()

    id2, type, dline = next (defs)
    id3, rlines = next (refs)

    dBuf = []
    rBuf = []

    maxId = 999999999

    for id1, path in vers:
        while id1 > id2:
            try:
                id2, type, dline = next (defs)
            except StopIteration:
                id2 = maxId

        while id1 > id3:
            try:
                id3, rlines = next (refs)
            except StopIteration:
                id3 = maxId

        if id1 == id2:
            dBuf.append ((path, type, dline))

        if id1 == id3:
            rBuf.append ((path, rlines))

    print ('Defined in', len (dBuf), 'files:')
    for path, type, dline in sorted (dBuf):
        print (path + ': ' + str (dline) + ' (' + type + ')')

    print()

    print ('Referenced in', len (rBuf), 'files:')
    for path, rlines in sorted (rBuf):
        print (path + ': ' + rlines)

else:
    print (argv[0] + ': Unknown subcommand: ' + cmd)
