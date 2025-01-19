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

from .query import get_query
from .lib import validFamily
from .web_utils import validate_version

class ApiIdentGetterResource:
    def on_get(self, req, resp, project, ident):
        version = validate_version(req.get_param('version'))
        if version is None:
            raise falcon.HTTPInvalidParam('', 'version')

        family = req.get_param('family')
        if not validFamily(family):
            family = 'C'

        query = get_query(req.context.config.project_dir, project)
        if not query:
            resp.status = falcon.HTTP_NOT_FOUND
            return

        if version == 'latest':
            version = query.query('latest')

        symbol_definitions, symbol_references, symbol_doccomments, peaks = query.query('ident', version, ident, family)

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {
            'definitions': [sym.__dict__ for sym in symbol_definitions],
            'references': [sym.__dict__ for sym in symbol_references],
            'documentations': [sym.__dict__ for sym in symbol_doccomments],
            'peeks': peaks
        }

        query.close()

