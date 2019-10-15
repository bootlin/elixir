import json
import os

import falcon

ELIXIR_DIR = os.path.dirname(__file__) + '/..'

def build_query(env, project):
    basedir = env['LXR_PROJ_DIR']
    os.environ['LXR_DATA_DIR'] = basedir + '/' + project + '/data'
    os.environ['LXR_REPO_DIR'] = basedir + '/' + project + '/repo'

    import sys
    sys.path = [ ELIXIR_DIR ] + sys.path
    import query
    return query.query

def call_query(query, *args):
    cwd = os.getcwd()
    os.chdir (ELIXIR_DIR)
    ret = query(*args)
    os.chdir (cwd)

    return ret


class IdentResource:
    def on_get(self, req, resp, project, ident):
        query = build_query(req.env, project)
        if 'version' in req.params:
            version = req.params['version']
        else:
            raise falcon.HTTPMissingParam('version')
        
        if version == 'latest':
            version = call_query(query, 'latest')

        symbol_definitions, symbol_references = call_query (query, 'ident', version, ident)
        if len(symbol_definitions) or len(symbol_references):
            resp.body = json.dumps(
                {
                    'definitions': [sym.__dict__ for sym in symbol_definitions],
                    'references': [sym.__dict__ for sym in symbol_references]
                })
            resp.status = falcon.HTTP_200
        else:
            raise falcon.HTTPNotFound({'title': 'Requested identifier not found in {} project'.format(project)})


application = falcon.API()

idents = IdentResource()

application.add_route('/ident/{project}/{ident}', idents)
