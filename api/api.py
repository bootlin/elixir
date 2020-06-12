#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2019--2020 Carmeli Tamir and contributors.
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

import json
import os

import falcon
from urllib import parse

ELIXIR_DIR = os.path.dirname(os.path.realpath(__file__)) + '/..'

def build_query(env, project):
    try:
        basedir = env['LXR_PROJ_DIR']
    except KeyError:
        basedir = os.environ['LXR_PROJ_DIR']
        # fail if it's not defined either place

    os.environ['LXR_DATA_DIR']= basedir + '/' + project + '/data'
    os.environ['LXR_REPO_DIR'] = basedir + '/' + project + '/repo'

    import sys
    sys.path = [ ELIXIR_DIR ] + sys.path
    import query
    return query.query

class IdentGetter:
    def on_get(self, req, resp, project, ident):
        query = build_query(req.env, project)
        if 'version' in req.params:
            version = req.params['version']
        else:
            raise falcon.HTTPMissingParam('version')

        if version == 'latest':
            version = query('latest')

        if 'family' in req.params:
            family = req.params['family']
        else:
            family = 'C'

        if family == 'B': #DT compatible strings are quoted in the database
            ident = parse.quote(ident)

        symbol_definitions, symbol_references, symbol_doccomments = query('ident', version, ident, family)
        resp.body = json.dumps(
            {
                'definitions': [sym.__dict__ for sym in symbol_definitions],
                'references': [sym.__dict__ for sym in symbol_references],
                'documentations': [sym.__dict__ for sym in symbol_doccomments]
            })
        resp.status = falcon.HTTP_200

def create_ident_getter():
    application = falcon.API()
    idents = IdentGetter()
    application.add_route('/ident/{project}/{ident}', idents)
    return application

application = create_ident_getter()
