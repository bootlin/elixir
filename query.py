#!/usr/bin/python3

import lib

p = lib.script ('list-tags')
p = b'\n'.join (p)
p = p.decode()
print (p)
