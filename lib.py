#!/usr/bin/python3

from subprocess import run, PIPE

def echo (bstr):
    print (bstr.decode(), end='')

def script (*args):
    p = run (('./script.sh',) + args, stdout=PIPE)
    p = p.stdout
    return p

def script_lines (*args):
    p = script (args)
    p = p.split (b'\n')
    return p
