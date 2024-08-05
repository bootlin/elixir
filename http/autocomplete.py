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

import falcon
from urllib import parse
import sys
import os

ELIXIR_DIR = os.path.dirname(os.path.realpath(__file__)) + '/..'

if ELIXIR_DIR not in sys.path:
    sys.path = [ ELIXIR_DIR ] + sys.path

import query

class AutocompleteResource:
    def on_get(self, req, resp):
        # Get values from http GET
        query_string = req.get_param('q')
        query_family = req.get_param('f')
        query_project = req.get_param('p')

        # Get project dirs
        basedir = req.env['LXR_PROJ_DIR']
        datadir = basedir + '/' + query_project + '/data'
        repodir = basedir + '/' + query_project + '/repo'

        q = query.Query(datadir, repodir)

        # Create tmp directory for autocomplete
        tmpdir = '/tmp/autocomplete/' + query_project
        if not(os.path.isdir(tmpdir)):
            os.makedirs(tmpdir, exist_ok=True)

        latest = q.query('latest')

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
            f.write('\n'.join([process(x.decode()) for x in q.query('keys', name)]))
            f.seek(0)
            f.readline() # Skip first line that store the version number

        # Prepare http response
        response = '['

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
        resp.text = response
        resp.status = falcon.HTTP_200

        # Close tmp file
        f.close()

def get_application():
    app = falcon.App()
    app.add_route('/', AutocompleteResource())
    return app

application = get_application()

