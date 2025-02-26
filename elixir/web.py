#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017--2020 Mikaël Bouillot <mikael.bouillot@bootlin.com>
#  and contributors.
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

import logging
import os
import sys
import re
import threading
import time
import datetime
from collections import OrderedDict, namedtuple
from re import search, sub
from typing import Any, Callable, Dict, NamedTuple, Tuple
from urllib import parse
import falcon
import jinja2

from .lib import validFamily
from .query import Query, SymbolInstance
from .filters import get_filters
from .filters.utils import FilterContext
from .autocomplete import AutocompleteResource
from .api import ApiIdentGetterResource
from .query import get_query
from .web_utils import ProjectConverter, IdentConverter, validate_version, validate_project, validate_ident, \
        get_elixir_version_string, get_elixir_repo_url, RequestContext, Config

VERSION_CACHE_DURATION_SECONDS = 2 * 60  # 2 minutes
ADD_ISSUE_LINK = "https://github.com/bootlin/elixir/issues/new"
ELIXIR_VERSION_STRING = get_elixir_version_string()
ELIXIR_REPO_LINK = get_elixir_repo_url(ELIXIR_VERSION_STRING)

DEFAULT_PROJECT = 'linux'

# Error with extra information about browsed project,
# to be used in project/version URLs
class ElixirProjectError(falcon.errors.HTTPError):
    def __init__(self, title, description, project=None, version=None, query=None,
                 status=falcon.HTTP_BAD_REQUEST, extra_template_args={}, **kwargs):
        self.project = project
        self.version = version
        self.query = query
        self.extra_template_args = extra_template_args
        super().__init__(status, title=title, description=description, **kwargs)

# Generate a summary of error details for a bug report
def generate_error_details(req, resp, title, details):
    return f"Request date: {datetime.datetime.now()}\n" + \
           f"Path: {req.path}\n" + \
           f"Query string: {req.query_string}\n" + \
           f"Method: {req.method}\n" + \
           f"Status code: {resp.status}\n" + \
           f"Error title: {title}\n" + \
           f"Error details: {details}\n"

def get_github_issue_url(details: str):
    body = ("TODO: add information on how you reached the error here and " +
            "validate the details below.\n\n" +
            "---\n\n" +
            details)

    return ADD_ISSUE_LINK + "?body=" + parse.quote(body)


# Generate an error page from ElixirProjectError
def get_project_error_page(req, resp, exception: ElixirProjectError):
    report_error_details = generate_error_details(req, resp, exception.title, exception.description)

    template_ctx = {
        'projects': get_projects(req.context.config.project_dir),
        'topbar_families': TOPBAR_FAMILIES,
        'current_version_path': (None, None, None),
        'current_family': 'A',
        'source_base_url': '/',
        'elixir_version_string': req.context.config.version_string,
        'elixir_repo_url': req.context.config.repo_url,

        'referer': req.referer if req.referer != req.uri else None,
        'bug_report_url': get_github_issue_url(report_error_details),
        'home_page_url': '/',
        'report_error_details': report_error_details,

        'error_title': exception.title,
    }

    if exception.project is not None and exception.query is not None:
        # Add details about current project
        query = exception.query
        project = exception.project
        version = exception.version

        versions_raw = get_versions_cached(query, req.context, project)
        get_url_with_new_version = lambda v: stringify_source_path(project, v, '/')
        versions, current_version_path = get_versions(versions_raw, get_url_with_new_version, version)

        if current_version_path[2] is None:
            # If details about current version are not available, make base links
            # point to latest.
            # current_tag is not set to latest to avoid latest being highlighted in the sidebar
            version = query.query('latest')

        template_ctx = {
            **template_ctx,

            'current_project': project,
            'current_tag': version,
            'versions': versions,
            'current_version_path': current_version_path,

            'home_page_url': get_source_base_url(project, version),
            'source_base_url': get_source_base_url(project, version),
            'ident_base_url': get_ident_base_url(project, version),
        }

    if exception.description is not None:
        template_ctx['error_details'] = exception.description

    template_ctx = {
        **template_ctx,
        **exception.extra_template_args,
    }

    template = req.context.jinja_env.get_template('error.html')
    result = template.render(template_ctx)

    if exception.query is not None:
        exception.query.close()

    return result

# Generate an error page from falcon exceptions
def get_error_page(req, resp, exception: ElixirProjectError):
    report_error_details = generate_error_details(req, resp, exception.title, exception.description)

    template_ctx = {
        'projects': get_projects(req.context.config.project_dir),
        'topbar_families': TOPBAR_FAMILIES,
        'current_version_path': (None, None, None),
        'current_family': 'A',
        'source_base_url': '/',

        'referer': req.referer,
        'bug_report_url': ADD_ISSUE_LINK + parse.quote(report_error_details),
        'report_error_details': report_error_details,

        'error_title': exception.title,
    }

    if exception.description is not None:
        template_ctx['error_details'] = exception.description

    template = req.context.jinja_env.get_template('error.html')
    return template.render(template_ctx)

# Validates project and version, returns project, version and query.
# To be used in project/version URLs
def validate_project_and_version(ctx, project, version):
    project = validate_project(parse.unquote(project))
    if project is None:
        raise ElixirProjectError('Error', 'Invalid project name')

    query = get_query(ctx.config.project_dir, project)
    if not query:
        raise ElixirProjectError('Error', 'Unknown project', status=falcon.HTTP_NOT_FOUND)

    version = validate_version(parse.unquote(version))
    if version is None:
        raise ElixirProjectError('Error', 'Invalid version', project=project, query=query)

    return project, version, query


# Returns base url of source pages
# project and version are assumed to be unquoted
def get_source_base_url(project: str, version: str) -> str:
    return f'/{ parse.quote(project, safe="") }/{ parse.quote(version, safe="") }/source'

# Converts ParsedSourcePath to a string with corresponding URL path
def stringify_source_path(project: str, version: str, path: str) -> str:
    if not path.startswith('/'):
        path = '/' + path
    path = f'{ get_source_base_url(project, version) }{ path }'
    return path.rstrip('/')

# Handles the '/' URL
class IndexResource:
    def on_get(self, req, resp):
        ctx = req.context
        project = DEFAULT_PROJECT

        query = get_query(ctx.config.project_dir, project)
        if not query:
            raise ElixirProjectError('Error', f'Unknown default project: {project}',
                                     status=falcon.HTTP_INTERNAL_SERVER_ERROR)

        version = query.query('latest')
        resp.status = falcon.HTTP_FOUND
        resp.location = stringify_source_path(project, version, '/')
        return

# Handles source URLs
# Path parameters are asssumed to be unquoted by converters
class SourceResource:
    def on_get(self, req, resp, project: str, version: str, path: str):
        project, version, query = validate_project_and_version(req.context, project, version)

        if not path.startswith('/') and len(path) != 0:
            path = f'/{ path }'

        if path.endswith('/'):
            resp.status = falcon.HTTP_MOVED_PERMANENTLY
            resp.location = stringify_source_path(project, version, path)
            return

        # Check if path contains only allowed characters
        if not search('^[A-Za-z0-9_/.,+-]*$', path):
            raise ElixirProjectError('Error', 'Path contains characters that are not allowed',
                              project=project, version=version, query=query)

        if version == 'latest':
            version = query.query('latest')
            resp.status = falcon.HTTP_FOUND
            resp.location = stringify_source_path(project, version, path)
            return

        raw_param = req.get_param('raw')
        if raw_param is not None and raw_param.strip() != '0':
            generate_raw_source(resp, query, project, version, path)
        else:
            resp.content_type = falcon.MEDIA_HTML
            resp.status, resp.text = generate_source_page(req.context, query, project, version, path)

        query.close()

# Handles source URLs without a path, ex. '/u-boot/v2023.10/source'.
# Note lack of trailing slash
class SourceWithoutPathResource(SourceResource):
    def on_get(self, req, resp, project: str, version: str):
        return super().on_get(req, resp, project, version, '')


# Returns base url of ident pages
# project and version assumed unquoted
def get_ident_base_url(project: str, version: str, family: str|None = None) -> str:
    project = parse.quote(project, safe="")
    version = parse.quote(version, safe="")
    if family is not None:
        return f'/{ project }/{ version }/{ parse.quote(family, safe="") }/ident'
    else:
        return f'/{ project }/{ version }/ident'

# Converts ParsedIdentPath to a string with corresponding URL path
def stringify_ident_path(project, version, family, ident) -> str:
    path = f'{ get_ident_base_url(project, version, family) }/{ parse.quote(ident, safe="") }'
    return path.rstrip('/')

# Handles redirect on a POST to ident resource
class IdentPostRedirectResource:
    def on_get(self, req, resp, project, version, family=None, ident=None):
        project, version, _ = validate_project_and_version(req.context, project, version)
        resp.status = falcon.HTTP_FOUND
        resp.location = stringify_source_path(project, version, "")

    def on_post(self, req, resp, project: str, version: str, family: str|None = None, _ident: str|None = None):
        project, version, query = validate_project_and_version(req.context, project, version)

        form = req.get_media()
        post_ident = form.get('i')
        post_family = form.get('f')

        if not validFamily(post_family):
            post_family = 'C'

        if not post_ident:
            raise ElixirProjectError('Error', 'Invalid identifier',
                              project=project, version=version, query=query,
                              extra_template_args={
                                  'searched_ident': parse.unquote(form.get('i')),
                                  'current_family': family,
                              })

        post_ident = post_ident.strip()
        resp.status = falcon.HTTP_MOVED_PERMANENTLY
        resp.location = stringify_ident_path(project, version, post_family, post_ident)

        query.close()

# Handles ident URLs when family is specified in the URL, both POST and GET
# See IdentPostRedirectResource for behavior on POST
# Path parameters are asssumed to be unquoted by converters
class IdentResource(IdentPostRedirectResource):
    def on_get(self, req, resp, project: str, version: str, family: str, ident: str):
        project, version, query = validate_project_and_version(req.context, project, version)

        family = parse.unquote(family)
        if not validFamily(family):
            family = 'C'

        ident = parse.unquote(ident)
        validated_ident = validate_ident(ident)
        if validated_ident is None:
            raise ElixirProjectError('Error', 'Invalid identifier',
                              project=project, version=version, query=query,
                              extra_template_args={
                                  'searched_ident': ident,
                                  'current_family': family,
                              })

        ident = validated_ident

        if version == 'latest':
            version = query.query('latest')
            resp.status = falcon.HTTP_FOUND
            resp.location = stringify_ident_path(project, version, family, ident)
            return

        resp.content_type = falcon.MEDIA_HTML
        resp.status, resp.text = generate_ident_page(req.context, query, project, version, family, ident)

        query.close()

# Handles ident URLs when family is not specified in the URL
# Also handles POST requests for ident URLs without family - IdentPostRedirectResource is
# inherited from IdentResource
class IdentWithoutFamilyResource(IdentResource):
    def on_get(self, req, resp, project: str, version: str, ident: str):
        super().on_get(req, resp, project, version, 'C', ident)

# Handles /{project}/{version} URL, without path
class IncompleteURLRedirectResource:
    def on_get(self, req, resp, project: str, version: str = "latest"):
        ctx = req.context

        query = get_query(ctx.config.project_dir, project)
        if not query:
            raise ElixirProjectError('Error', f'Unknown default project: {project}',
                                     status=falcon.HTTP_INTERNAL_SERVER_ERROR)

        if version == 'latest' or len(version) == 0:
            version = query.query('latest')

        resp.status = falcon.HTTP_FOUND
        resp.location = stringify_source_path(project, version, '/')

# Handles /{project}/{version}/... URLs with unknown "command"
class UnknownPathResource:
    def on_get(self, req, resp, project: str, version: str, family: str = "", subcmd: str = "", path: str = ""):
        project, version, query = validate_project_and_version(req.context, project, version)

        raise ElixirProjectError('Error', 'Invalid path',
                          project=project, version=version, query=query,
                          extra_template_args={
                              'current_family': 'A',
                          })


# File families available in the dropdown next to search input in the topbar
TOPBAR_FAMILIES = {
    'A': 'All symbols',
    'C': 'C/CPP/ASM',
    'K': 'Kconfig',
    'D': 'Devicetree',
    'B': 'DT compatible',
}

# Returns a list of names of top-level directories in basedir
def get_directories(basedir: str) -> list[str]:
    directories = []
    for filename in os.listdir(basedir):
        filepath = os.path.join(basedir, filename)
        if os.path.isdir(filepath):
            directories.append(filename)
    return sorted(directories)

# Tuple of project name and URL to root of that project
# Used to render project list
ProjectEntry = namedtuple('ProjectEntry', 'name, url')

# Returns a list of ProjectEntry tuples of projects stored in directory basedir
def get_projects(basedir: str) -> list[ProjectEntry]:
    return [ProjectEntry(p, f"/{p}/latest/source") for p in get_directories(basedir)]

# Tuple of version name and URL to chosen resource with that version
# Used to render version list in the sidebar
VersionEntry = namedtuple('VersionEntry', 'version, url')

# Takes result of Query.query('version') and prepares it for the sidebar template.
#  Returns an OrderedDict with version information and optionally a triple with
#  (major, minor, version) of current_version. The triple is useful, because sometimes
#  the major or minor of a version (in this context) is a custom string (ex. FIXME).
# versions: OrderedDict with major parts of versions as keys, values are OrderedDicts
#   with minor version parts as keys and complete version strings as values
# get_url: function that takes a version string and returns the URL
#   for that version. Meaning of the URL can depend on the context
# current_version: string with currently browsed version
def get_versions(versions: OrderedDict[str, OrderedDict[str, str]],
                 get_url: Callable[[str], str],
                 current_version: str) -> Tuple[dict[str, dict[str, list[VersionEntry]]], Tuple[str|None, str|None, str|None]]:

    result = OrderedDict()
    current_version_path = (None, None, None)
    for major, minor_verions in versions.items():
        for minor, patch_versions in minor_verions.items():
            for v in patch_versions:
                if major not in result:
                    result[major] = OrderedDict()
                if minor not in result[major]:
                    result[major][minor] = []
                result[major][minor].append(VersionEntry(v, get_url(v)))
                if v == current_version:
                    current_version_path = (major, minor, v)

    return result, current_version_path

# Caches get_versions result in a context object
def get_versions_cached(q, ctx, project):
    with ctx.versions_cache_lock:
        if project not in ctx.versions_cache:
            ctx.versions_cache[project] = (time.time(), q.query('versions'))
            cached_versions = ctx.versions_cache[project]
        else:
            cached_versions = ctx.versions_cache[project]
            if time.time()-cached_versions[0] > VERSION_CACHE_DURATION_SECONDS:
                ctx.versions_cache[project] = (time.time(), q.query('versions'))
                cached_versions = ctx.versions_cache[project]

        return cached_versions[1]

# Retruns template context used by the layout template
# get_url_with_new_version: see get_url parameter of get_versions
# project: name of the project
# version: version of the project
def get_layout_template_context(q: Query, ctx: RequestContext, get_url_with_new_version: Callable[[str], str],
                                project: str, version: str) -> dict[str, Any]:
    versions_raw = get_versions_cached(q, ctx, project)
    versions, current_version_path = get_versions(versions_raw, get_url_with_new_version, version)

    return {
        'projects': get_projects(ctx.config.project_dir),
        'versions': versions,
        'current_version_path': current_version_path,
        'topbar_families': TOPBAR_FAMILIES,
        'elixir_version_string': ctx.config.version_string,
        'elixir_repo_url': ctx.config.repo_url,

        'source_base_url': get_source_base_url(project, version),
        'ident_base_url': get_ident_base_url(project, version),
        'current_project': project,
        'current_tag': parse.unquote(version),
        'current_family': 'A',
    }

# Generate raw source response
def generate_raw_source(resp, query, project, version, path):
    type = query.query('type', version, path)
    if type != 'blob':
        raise ElixirProjectError('File not found', 'This file does not exist.',
                                 query=query, project=project, version=version)
    else:
        code = query.get_file_raw(version, path)
        resp.content_type = 'application/octet-stream'
        resp.text = code
        resp.downloadable_as = path.split('/')[-1]
        # Cache for 24 hours
        resp.cache_control = ('max-age=86400',)
        # Sandbox result just in case
        resp.headers['Content-Security-Policy'] = "sandbox; default-src 'none'"

# Guesses file format based on filename, returns code formatted as HTML
def format_code(filename: str, code: str) -> str:
    import pygments
    import pygments.lexers
    import pygments.formatters
    from pygments.lexers.asm import GasLexer
    from pygments.lexers.r import SLexer

    try:
        lexer = pygments.lexers.guess_lexer_for_filename(filename, code)
        if filename.endswith('.S') and isinstance(lexer, SLexer):
            lexer = GasLexer()
    except pygments.util.ClassNotFound:
        lexer = pygments.lexers.get_lexer_by_name('text')

    lexer.stripnl = False
    formatter = pygments.formatters.HtmlFormatter(
        # Adds line numbers column to output
        linenos=True,
        # Wraps line numbers in link (a) tags
        anchorlinenos=True,
        # Wraps each line in a span tag with id='codeline-{line_number}'
        linespans='codeline',
    )
    return pygments.highlight(code, lexer, formatter)

# Generate formatted HTML of a file, apply filters (for ex. to add identifier links)
# q: Query object
# project: name of the requested project
# version: requested version of the project
# path: path to the file in the repository
def generate_source(q: Query, project: str, version: str, path: str) -> str:
    code = q.query('file', version, path)

    _, fname = os.path.split(path)
    _, extension = os.path.splitext(fname)
    extension = extension[1:].lower()
    family = q.query('family', fname)

    source_base_url = get_source_base_url(project, version)

    def get_ident_url(ident, ident_family=None):
        if ident_family is None:
            ident_family = family
        return stringify_ident_path(project, version, ident_family, ident)

    filter_ctx = FilterContext(
        q,
        version,
        family,
        path,
        get_ident_url,
        lambda path: f'{ source_base_url }{ "/" if not path.startswith("/") else "" }{ path }',
        lambda rel_path: f'{ source_base_url }{ os.path.dirname(path) }/{ rel_path }',
    )

    filters = get_filters(filter_ctx, project)

    # Apply filters
    for f in filters:
        code = f.transform_raw_code(filter_ctx, code)

    html_code_block = format_code(fname, code)

    # Replace line numbers by links to the corresponding line in the current file
    html_code_block = sub('href="#codeline-(\d+)', 'name="L\\1" id="L\\1" href="#L\\1', html_code_block)

    for f in filters:
        html_code_block = f.untransform_formatted_code(filter_ctx, html_code_block)

    return html_code_block

# Represents a file entry in git tree
# type : either tree (directory), blob (file) or symlink
# name: filename of the file
# path: path of the file, path to the target in case of symlinks
# url: absolute URL of the file
# size: int, file size in bytes, None for directories and symlinks
DirectoryEntry = namedtuple('DirectoryEntry', 'type, name, path, url, size')

# Returns a list of DirectoryEntry objects with information about files in a directory
# base_url: file URLs will be created by appending file path to this URL. It shouldn't end with a slash
# tag: requested repository tag
# path: path to the directory in the repository
def get_directory_entries(q: Query, base_url, tag: str, path: str) -> list[DirectoryEntry]:
    dir_entries = []
    lines = q.query('dir', tag, path)

    for l in lines:
        type, name, size, perm = l.split(' ')
        file_path = f"{ path }/{ name }"

        if type == 'tree':
            dir_entries.append(DirectoryEntry('tree', name, file_path, f"{ base_url }{ file_path }", None))
        elif type == 'blob':
            # 120000 permission means it's a symlink
            if perm == '120000':
                dir_path = path if path.endswith('/') else path + '/'
                link_contents = q.get_file_raw(tag, file_path)
                link_target_path = os.path.abspath(dir_path + link_contents)

                dir_entries.append(DirectoryEntry('symlink', name, link_target_path, f"{ base_url }{ link_target_path }", size))
            else:
                dir_entries.append(DirectoryEntry('blob', name, file_path, f"{ base_url }{ file_path }", size))

    return dir_entries

# Generates response (status code and optionally HTML) of the `source` route
def generate_source_page(ctx: RequestContext, q: Query,
                         project: str, version: str, path: str) -> tuple[int, str]:

    status = falcon.HTTP_OK
    source_base_url = get_source_base_url(project, version)

    type = q.query('type', version, path)

    # Generate breadcrumbs
    path_split = path.split('/')[1:]
    path_temp = ''
    breadcrumb_urls = []
    for p in path_split:
        path_temp += '/'+p
        breadcrumb_urls.append((p, f'{ source_base_url }{ path_temp }'))

    if type == 'tree':
        back_path = os.path.dirname(path[:-1])
        if back_path == '/':
            back_path = ''

        template_ctx = {
            'dir_entries': get_directory_entries(q, source_base_url, version, path),
            'back_url': f'{ source_base_url }{ back_path }' if path != '' else None,
        }
        template = ctx.jinja_env.get_template('tree.html')
    elif type == 'blob':
        template_ctx = {
            'code': generate_source(q, project, version, path),
            'path': path,
        }
        template = ctx.jinja_env.get_template('source.html')
    else:
        raise ElixirProjectError('File not found', 'This file does not exist.',
                                 status=falcon.HTTP_NOT_FOUND,
                                 query=q, project=project, version=version,
                                 extra_template_args={'breadcrumb_urls': breadcrumb_urls})

    # Create titles like this:
    # root path: "Linux source code (v5.5.6) - Bootlin"
    # first level path: "arch - Linux source code (v5.5.6) - Bootlin"
    # deeper paths: "Makefile - arch/um/Makefile - Linux source code (v5.5.6) - Bootlin"
    if path == '':
        title_path = ''
    elif len(path_split) == 1:
        title_path = f'{ path_split[0] } - '
    else:
        title_path = f'{ path_split[-1] } - { "/".join(path_split) } - '

    get_url_with_new_version = lambda v: stringify_source_path(project, v, path)

    # Create template context
    data = {
        **get_layout_template_context(q, ctx, get_url_with_new_version, project, version),

        'title_path': title_path,
        'path': path,
        'breadcrumb_urls': breadcrumb_urls,

        **template_ctx,
    }

    return (status, template.render(data))

# Represents line in a file with URL to that line
LineWithURL = namedtuple('LineWithURL', 'lineno, url')

# Represents a symbol occurrence to be rendered by ident template
# type : type of the symbol
# path: path of the file that contains the symbol
# line: list of LineWithURL
# peeks: map of code line previews for this path
SymbolEntry = namedtuple('SymbolEntry', 'type, path, lines, peeks')

# Converts SymbolInstance into SymbolEntry
# path of SymbolInstance will be appended to base_url
def symbol_instance_to_entry(base_url: str, symbol: SymbolInstance, peeks: Dict[str, Dict[int, str]]) -> SymbolEntry:
    # TODO this should be a responsibility of Query
    if type(symbol.line) is str:
        line_numbers = symbol.line.split(',')
    else:
        line_numbers = [symbol.line]

    lines = [
        LineWithURL(int(l), f'{ base_url }/{ symbol.path }#L{ l }')
        for l in line_numbers
    ]

    current_peeks = peeks.get(symbol.path, {})

    return SymbolEntry(symbol.type, symbol.path, lines, current_peeks)

# Generates response (status code and optionally HTML) of the `ident` route
# basedir: path to data directory, ex: "/srv/elixir-data"
def generate_ident_page(ctx: RequestContext, q: Query,
                        project: str, version: str, family: str, ident: str) -> tuple[int, str]:

    status = falcon.HTTP_OK
    source_base_url = get_source_base_url(project, version)

    symbol_definitions, symbol_references, symbol_doccomments, peeks = q.query('ident', version, ident, family)

    symbol_sections = []
    empty_peeks = {}

    if len(symbol_definitions) or len(symbol_references):
        if len(symbol_doccomments):
            symbol_sections.append({
                'title': 'Documented',
                'symbols': {'_unknown': [symbol_instance_to_entry(source_base_url, sym, empty_peeks) for sym in symbol_doccomments]},
            })

        if len(symbol_definitions):
            defs_by_type = OrderedDict({})

            # TODO this should be a responsibility of Query
            for sym in symbol_definitions:
                if sym.type not in defs_by_type:
                    defs_by_type[sym.type] = [symbol_instance_to_entry(source_base_url, sym, peeks)]
                else:
                    defs_by_type[sym.type].append(symbol_instance_to_entry(source_base_url, sym, peeks))

            symbol_sections.append({
                'title': 'Defined',
                'symbols': defs_by_type,
            })
        else:
            symbol_sections.append({
                'message': 'No definitions found in the database',
            })

        if len(symbol_references):
            symbol_sections.append({
                'title': 'Referenced',
                'symbols': {'_unknown': [symbol_instance_to_entry(source_base_url, sym, peeks) for sym in symbol_references]},
            })
        else:
            symbol_sections.append({
                'message': 'No references found in the database',
            })

    else:
        if ident != '':
            status = falcon.HTTP_NOT_FOUND

    get_url_with_new_version = lambda v: stringify_ident_path(project, v, family, ident)

    data = {
        **get_layout_template_context(q, ctx, get_url_with_new_version, project, version),

        'searched_ident': ident,
        'current_family': family,

        'symbol_sections': symbol_sections,
    }

    template = ctx.jinja_env.get_template('ident.html')
    return (status, template.render(data))


def get_jinja_env():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    templates_dir = os.path.join(script_dir, '../templates/')
    loader = jinja2.FileSystemLoader(templates_dir)
    return jinja2.Environment(loader=loader)

# see https://falcon.readthedocs.io/en/v3.1.2/user/recipes/raw-url-path.html
# Replaces the default, unquoted URL with a quoted version
# NOTE: this is non-standard and it's not guaranteed to work on all WSGI servers
class RawPathComponent:
    def process_request(self, req, _):
        raw_uri = req.env.get('RAW_URI') or req.env.get('REQUEST_URI')
        if raw_uri:
            req.path, _, _ = raw_uri.partition('?')

# Adds request context to all requests
class RequestContextMiddleware:
    def __init__(self, jinja_env):
        self.jinja_env = jinja_env
        self.versions_cache = {}
        self.versions_cache_lock = threading.Lock()

    def process_request(self, req, _resp):
        req.context = RequestContext(
            Config(req.env['LXR_PROJ_DIR'], ELIXIR_VERSION_STRING, ELIXIR_REPO_LINK),
            self.jinja_env,
            logging.getLogger(__name__),
            self.versions_cache,
            self.versions_cache_lock,
        )

# Serialies caught exceptions to JSON or HTML
# See https://falcon.readthedocs.io/en/stable/api/app.html#falcon.App.set_error_serializer
def error_serializer(req, resp, exception):
    preferred = req.client_prefers((falcon.MEDIA_HTML, falcon.MEDIA_JSON))

    if preferred is not None:
        if preferred == falcon.MEDIA_JSON:
            resp.data = exception.to_json()
            resp.content_type = falcon.MEDIA_JSON
        elif preferred == falcon.MEDIA_HTML:
            if isinstance(exception, ElixirProjectError):
                resp.text = get_project_error_page(req, resp, exception)
            else:
                resp.text = get_error_page(req, resp, exception)
            resp.content_type = falcon.MEDIA_HTML

    resp.append_header('Vary', 'Accept')

# Builds and returns the Falcon application
def get_application():
    app = falcon.App(middleware=[
        RawPathComponent(),
        RequestContextMiddleware(get_jinja_env()),
    ])

    app.router_options.converters['project'] = ProjectConverter
    app.router_options.converters['ident'] = IdentConverter

    app.set_error_serializer(error_serializer)

    app.add_route('/', IndexResource())
    app.add_route('/{project}/{version}/source/{path:path}', SourceResource())
    app.add_route('/{project}/{version}/source', SourceWithoutPathResource())
    app.add_route('/{project}/{version}/ident', IdentPostRedirectResource())
    app.add_route('/{project}/{version}/ident/{ident}', IdentWithoutFamilyResource())
    app.add_route('/{project}/{version}/{family}/ident/{ident}', IdentResource())

    app.add_route('/acp', AutocompleteResource())
    app.add_route('/api/ident/{project:project}/{ident:ident}', ApiIdentGetterResource())

    app.add_route('/{project}', IncompleteURLRedirectResource())
    app.add_route('/{project}/{version}', IncompleteURLRedirectResource())
    app.add_route('/{project}/{version}/', IncompleteURLRedirectResource())
    app.add_route('/{project}/{version}/{family}', UnknownPathResource())
    app.add_route('/{project}/{version}/{family}/{subcmd}', UnknownPathResource())
    app.add_route('/{project}/{version}/{family}/{subcmd}/{path:path}', UnknownPathResource())

    return app

application = get_application()

