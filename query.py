#!/usr/bin/python3

from sys import argv
from lib import echo, script, scriptLines, unescape

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
        del tokens[-1]
        toBe = True
        for tok in tokens:
            toBe = not toBe
            if toBe:
                tok = b'\033[31m' + tok + b'\033[0m'
            else:
                tok = unescape (tok)
            echo (tok)
    else:
        p = script ('get-file', version, path)
        echo (p)

elif cmd == 'ident':
    version = argv[2]
    ident = argv[3]

    pass

else:
    print (argv[0] + ': Unknown subcommand: ' + cmd)
