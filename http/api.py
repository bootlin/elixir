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
import sys

ELIXIR_DIR = os.path.dirname(os.path.realpath(__file__)) + '/..'

if ELIXIR_DIR not in sys.path:
    sys.path = [ ELIXIR_DIR ] + sys.path

import query

class ApiIdentGetterResource:
    def on_get(self, req, resp, project, ident):
        try:
            basedir = req.env['LXR_PROJ_DIR']
        except KeyError:
            basedir = os.environ['LXR_PROJ_DIR']

        data_dir = basedir + '/' + project + '/data'
        repo_dir = basedir + '/' + project + '/repo'

        q = query.Query(data_dir, repo_dir)

        if 'version' in req.params:
            version = req.params['version']
        else:
            raise falcon.HTTPMissingParam('version')

        if version == 'latest':
            version = q.query('latest')

        if 'family' in req.params:
            family = req.params['family']
        else:
            family = 'C'

        symbol_definitions, symbol_references, symbol_doccomments = q.query('ident', version, ident, family)

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {
            'definitions': [sym.__dict__ for sym in symbol_definitions],
            'references': [sym.__dict__ for sym in symbol_references],
            'documentations': [sym.__dict__ for sym in symbol_doccomments]
        }

        q.close()

