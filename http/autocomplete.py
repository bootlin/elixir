#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017--2020 Maxime Chretien <maxime.chretien@bootlin.com>
#                           and contributors.
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

import cgi
import cgitb
from urllib import parse
import sys
import os

# Get values from http GET
form = cgi.FieldStorage()
query_string = form.getvalue('q')
query_family = form.getvalue('f')
query_project = form.getvalue('p')

# Get project dirs
basedir = os.environ['LXR_PROJ_DIR']
os.environ['LXR_DATA_DIR'] = basedir + '/' + query_project + '/data'
os.environ['LXR_REPO_DIR'] = basedir + '/' + query_project + '/repo'

# Import query
sys.path = [ sys.path[0] + '/..' ] + sys.path
from query import query

# Create tmp directory for autocomplete
tmpdir = '/tmp/autocomplete/' + query_project
if not(os.path.isdir(tmpdir)):
    os.makedirs(tmpdir, exist_ok=True)

latest = query('latest')

# Define some specific values for some families
if query_family == 'B':
    name = 'comps'
    process = lambda x: parse.unquote(x)
else:
    name = 'defs'
    process = lambda x: x

# Init values for tmp files
filename = tmpdir + '/' + name
mode = 'r+' if os.path.exists(filename) else 'w+'

# Open tmp file
# Fill it with the keys of the database only
# if the file is older than the database
f = open(filename, mode)
if not f.readline()[:-1] == latest:
    f.seek(0)
    f.truncate()
    f.write(latest + "\n")
    f.write('\n'.join([process(x.decode()) for x in query('keys', name)]))
    f.seek(0)
    f.readline() # Skip first line that store the version number

# Prepare http response
response = 'Content-Type: text/html;charset=utf-8\n\n[\n'

# Search for the 10 first matching elements in the tmp file
index = 0
for i in f:
    if i.startswith(query_string):
        response += '"' + i[:-1] + '",'
        index += 1

    if index == 10:
        break

# Complete and send response
response = response[:-1] + ']'
print(response)

# Close tmp file
f.close()
