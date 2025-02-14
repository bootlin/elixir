import os
import re
import logging
import threading
from urllib import parse
from typing import Any, Dict, NamedTuple
import falcon
import jinja2

from .lib import validFamily, run_cmd

ELIXIR_DIR = os.path.normpath(os.path.dirname(__file__) + "/../")
ELIXIR_REPO_LINK = 'https://github.com/bootlin/elixir/'

def get_elixir_version_string():
    version = os.environ.get('ELIXIR_VERSION')
    if version is not None and len(version) != 0:
        return version

    try:
        # try to get Elixir version from git
        result, return_code = run_cmd('git',
            '-C', ELIXIR_DIR,
            '-c', f'safe.directory={ ELIXIR_DIR }',
            'rev-parse', '--short', 'HEAD'
        )

        if return_code == 0:
            return result.decode('utf-8')

    except Exception:
        logging.exception("failed to get elixir commit hash")

    return ''

def get_elixir_repo_url(version):
    if re.match('^[0-9a-f]{5,12}$', version) or version.startswith('v'):
        return ELIXIR_REPO_LINK + f'tree/{ version }'
    else:
        return ELIXIR_REPO_LINK

# Elixir config, currently contains only path to directory with projects
class Config(NamedTuple):
    project_dir: str
    version_string: str
    repo_url: str

# Basic information about handled request - current Elixir configuration, configured Jinja environment
# and logger
class RequestContext(NamedTuple):
    config: Config
    jinja_env: jinja2.Environment
    logger: logging.Logger
    versions_cache: Dict[str, str]
    versions_cache_lock: threading.Lock

def validate_project(project: str) -> str|None:
    if project is not None and re.match(r'^[a-zA-Z0-9_.,:/-]+$', project):
        return project.strip()

# Validates and unquotes project parameter
class ProjectConverter(falcon.routing.BaseConverter):
    def convert(self, value: str) -> str:
        value = parse.unquote(value)
        project = validate_project(value)
        if project is None:
            raise falcon.HTTPBadRequest('Error', 'Invalid project name')
        return project

def validate_version(version) -> str|None:
    if version is not None and re.match(r'^[a-zA-Z0-9_.,:/-]+$', version):
        return version.strip()

def validate_ident(ident: str) -> str|None:
    if ident is not None and re.match(r'^[A-Za-z0-9_,.+?#-]+$', ident):
        return ident.strip()

# Validates and unquotes identifier parameter
class IdentConverter(falcon.routing.BaseConverter):
    def convert(self, value: str) -> str|None:
        value = parse.unquote(value)
        return validate_ident(value)

