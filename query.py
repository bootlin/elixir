#!/usr/bin/python3

from sys import argv
from lib import echo, script

cmd = argv[1]

if cmd == 'versions':
    p = script ('list-tags')
    echo (p)

elif cmd == 'dir':
    version = argv[2]
    path = argv[3]
    p = script ('get-dir', version, path)
    echo (p)

elif cmd == 'source':
    version = argv[2]
    path = argv[3]

    pass

elif cmd == 'ident':
    version = argv[2]
    ident = argv[3]

    pass

else:
    print (argv[0] + ': Unknown subcommand: ' + cmd)
