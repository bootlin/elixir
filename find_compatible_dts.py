#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017--2020  Maxime Chretien
#  <maxime.chretien@bootlin.com> and contributors
#
#  Elixir is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Elixir is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Elixir.  If not, see <http://www.gnu.org/licenses/>.

from sys import argv
import re
import os
from urllib import parse
import query

usage_message = ("USAGE: find_compatible_dts.py <file> <family>\n"
                 "file : The file you want to search in\n"
                 "family : The type of file (C for .c/.cpp/.h/...\n"
                 "                           D for .dts/.dtsi\n"
                 "                           B for bindings docs files)")

ident_list = ""

def parse_c(content):
    return re.findall("\s*{*\s*\.compatible\s*=\s*\"(.+?)\"", content)

def parse_dts(content):
    ret = []
    if re.match("\s*compatible", content) != None:
        ret = re.findall("\"(.+?)\"", content)
    return ret

def parse_bindings(content):
    # There are a lot of wrong results
    # but we don't apply that to a lot of files
    # so it should be fine
    return re.findall("([\w-]+,?[\w-]+)", content)


# Main
# Test and get args
if len(argv) < 3:
    print("ERROR: Missing arguments !\n" + usage_message)
    exit(1)

filename = argv[1]
family = argv[2]

# Make sure it's an accepted family
if not family in ['C', 'D', 'B']:
    print("ERROR: Unknown family !\n" + usage_message)
    exit(1)

# Make sure file exists
try:
    f = open(filename, 'rb')
except IOError:
    print("ERROR: File doesn't exist !\n" + usage_message)
    exit(1)

# Iterate though lines and search for idents
for num, line in enumerate(f, 1):
    line = query.decode(line)
    if family == 'C':
        ret = parse_c(line)
    elif family == 'D':
        ret = parse_dts(line)
    elif family == 'B':
        ret = parse_bindings(line)

    for i in range(len(ret)):
        ident_list += str(parse.quote(ret[i])) + ' ' + str(num) + '\n'

# Print the list and exit
print(ident_list, end='')
exit(0)
