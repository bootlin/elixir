import os
import re
import logging
import threading
from urllib import parse
from typing import Any, Dict, NamedTuple
import falcon
import jinja2

from .lib import validFamily, run_cmd
from pygments.formatters import HtmlFormatter

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

def get_elixir_repo_link(version):
    if re.match('^[0-9a-f]{5,12}$', version) or version.startswith('v'):
        return ELIXIR_REPO_LINK + f'tree/{ version }'
    else:
        return ELIXIR_REPO_LINK

# Elixir config, currently contains only path to directory with projects
class Config(NamedTuple):
    project_dir: str
    version_string: str
    repo_link: str

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

class DiffFormater(HtmlFormatter):
    def __init__(self, diff, left: bool, *args, **kwargs):
        self.diff = diff
        self.left = left
        super().__init__(*args[2:], **kwargs)

    def get_next_diff_line(self, diff_num, next_diff_line):
        next_diff = self.diff[diff_num] if len(self.diff) > diff_num else None
        if next_diff is not None:
            if next_diff[0] == '-' or next_diff[0] == '+':
                next_diff_line = next_diff[1]
            elif self.left and next_diff[0] == '=':
                next_diff_line = next_diff[1]
            elif not self.left and next_diff[0] == '=':
                next_diff_line = next_diff[3]

        return next_diff, diff_num+1, next_diff_line

    def mark_lines(self, source, num, css_class):
        i = 0
        while i < num:
            try:
                t, line = next(source)
            except StopIteration:
                break
            if t == 1:
                yield t, f'<span class="{css_class}">{line}</span>'
                i += 1
            else:
                yield t, line

    def yield_empty(self, num):
        for _ in range(num):
            yield 0, '<span class="diff-line">&nbsp;\n</span>'

    def wrap_diff(self, source):
        next_diff, diff_num, next_diff_line = self.get_next_diff_line(0, None)

        linenum = 1

        while True:
            try:
                line = next(source)
            except StopIteration:
                break

            yield line

            if linenum == next_diff_line:
                if next_diff is not None:
                    if self.left and next_diff[0] == '+':
                        yield from self.yield_empty(next_diff[2])
                    elif next_diff[0] == '+':
                        yield from self.mark_lines(source, next_diff[2], 'line-added')
                        linenum += next_diff[2]
                    elif not self.left and next_diff[0] == '-':
                        yield from self.yield_empty(next_diff[2])
                    elif next_diff[0] == '-':
                        yield from self.mark_lines(source, next_diff[2], 'line-removed')
                        linenum += next_diff[2]
                    elif next_diff[0] == '=':
                        total = max(next_diff[2], next_diff[4])
                        to_print = next_diff[2] if self.left else next_diff[4]
                        yield from self.mark_lines(source, to_print, 'line-removed' if self.left else 'line-added')
                        yield from self.yield_empty(total-to_print)
                        linenum += to_print

                next_diff, diff_num, next_diff_line = self.get_next_diff_line(diff_num, next_diff_line)

            linenum += 1

    def wrap(self, source):
        return super().wrap(self.wrap_diff(source))

