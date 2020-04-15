#!/usr/bin/env python3

import json
import os

import falcon

ELIXIR_DIR = os.path.dirname(__file__) + '/..'

def build_query(env, project):
    if 'LXR_DATA_DIR' not in os.environ or 'LXR_REPO_DIR' not in os.environ:
        basedir = env['LXR_PROJ_DIR']
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

        symbol_definitions, symbol_references, symbol_doccomments_UNUSED = query('ident', version, ident)
        resp.body = json.dumps(
            {
                'definitions': [sym.__dict__ for sym in symbol_definitions],
                'references': [sym.__dict__ for sym in symbol_references]
            })
        resp.status = falcon.HTTP_200

def create_ident_getter():
    application = falcon.API()
    idents = IdentGetter()
    application.add_route('/ident/{project}/{ident}', idents)
    return application

application = create_ident_getter()
