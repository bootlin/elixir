#!/usr/bin/python3

import subprocess

def script (*args):
    p = subprocess.run (('./script.sh',) + args, stdout=subprocess.PIPE)
    p = p.stdout.split (b'\n')
    del p[-1]
    return p
