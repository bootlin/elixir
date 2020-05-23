#!/usr/bin/env python3

import json
import os

import falcon

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

        symbol_definitions, symbol_references, symbol_doccomments_UNUSED = query('ident', version, ident, family)
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
