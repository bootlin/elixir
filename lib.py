#!/usr/bin/python3

from subprocess import run, PIPE

def echo (bstr):
    print (bstr.decode(), end='')

def script (*args):
    p = run (('./script.sh',) + args, stdout=PIPE)
    p = p.stdout
    return p

def scriptLines (*args):
    p = script (*args)
    p = p.split (b'\n')
    del p[-1]
    return p

def unescape (bstr):
    subs = (
        ('<','/*'),
        ('>','*/'),
        ('\1','\n'),
        ('\2','<'),
        ('\3','>'))
    for a,b in subs:
        a = a.encode()
        b = b.encode()
        bstr = bstr.replace (a, b)
    return bstr
