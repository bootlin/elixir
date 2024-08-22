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

import sys
import os
import json
from urllib import parse
from bsddb3.db import DB_SET_RANGE
import falcon

from .lib import autoBytes, validFamily
from .query import get_query
from .web_utils import validate_project, validate_ident

class AutocompleteResource:
    def on_get(self, req, resp):
        ident_prefix = req.get_param('q')
        family = req.get_param('f')
        project = req.get_param('p')

        ident_prefix = validate_ident(ident_prefix)
        if ident_prefix is None:
            raise falcon.HTTPInvalidParam('', 'ident')

        project = validate_project(project)
        if project is None:
            raise falcon.HTTPInvalidParam('', 'project')

        if not validFamily(family):
            family = 'C'

        query = get_query(req.context.config.project_dir, project)
        if not query:
            resp.status = falcon.HTTP_NOT_FOUND
            return

        if family == 'B':
            # DTS identifiers are stored quoted
            process = lambda x: parse.unquote(x)
            db = query.db.comps
        else:
            process = lambda x: x
            db = query.db.defs

        response = []

        i = 0
        cur = db.db.cursor()
        query_bytes = autoBytes(parse.quote(ident_prefix))
        # Find "the smallest key greater than or equal to the specified key"
        # https://docs.oracle.com/cd/E17276_01/html/api_reference/C/dbcget.html
        # In practice this should mean "the key that starts with provided prefix"
        # See docs about the default comparison function for B-Tree databases:
        # https://docs.oracle.com/cd/E17276_01/html/api_reference/C/dbset_bt_compare.html
        key, _ = cur.get(query_bytes, DB_SET_RANGE)
        while i <= 10:
            if key.startswith(query_bytes):
                # If found key starts with the prefix, add to response
                # and move to the next key
                i += 1
                response.append(process(key.decode("utf-8")))
                key, _ = cur.next()
            else:
                # If found key does not start with the prefix, stop
                break

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = response

