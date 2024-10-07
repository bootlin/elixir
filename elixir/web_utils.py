import os
import re
from urllib import parse
import logging
import falcon

from .lib import validFamily, run_cmd

ELIXIR_DIR = os.path.dirname(__file__)

def get_elixir_version_string():
    version = os.environ.get('ELIXIR_VERSION')
    if version is not None and len(version) != 0:
        return version

    try:
        # try to get Elixir version from git
        result, return_code = run_cmd('git',
            '-C', ELIXIR_DIR,
            '-c', f'safe.directory={ os.path.normpath(ELIXIR_DIR) }',
            'rev-parse', '--short', 'HEAD'
        )

        if return_code == 0:
            return result.decode('utf-8')

    except Exception:
        logging.exception("failed to get elixir commit hash")

    return ''

def validate_project(project):
    if project is not None and re.match(r'^[a-zA-Z0-9_.,:/-]+$', project):
        return project.strip()

# Validates and unquotes project parameter
class ProjectConverter(falcon.routing.BaseConverter):
    def convert(self, value: str):
        value = parse.unquote(value)
        project = validate_project(value)
        if project is None:
            raise falcon.HTTPBadRequest('Error', 'Invalid project name')
        return project

def validate_version(version):
    if version is not None and re.match(r'^[a-zA-Z0-9_.,:/-]+$', version):
        return version.strip()

def validate_ident(ident):
    if ident is not None and re.match(r'^[A-Za-z0-9_,.+?#-]+$', ident):
        return ident.strip()

# Validates and unquotes identifier parameter
class IdentConverter(falcon.routing.BaseConverter):
    def convert(self, value: str):
        value = parse.unquote(value)
        return validate_ident(value)

