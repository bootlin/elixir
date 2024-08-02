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

import cgi
import cgitb
import os
import re
import sys
from collections import OrderedDict, namedtuple
from re import search, sub
from urllib import parse
import jinja2

sys.path = [ sys.path[0] + '/..' ] + sys.path
from lib import validFamily
from query import Query, SymbolInstance
from filters import get_filters
from filters.utils import FilterContext

script_dir = os.path.dirname(os.path.realpath(__file__))
templates_dir = os.path.join(script_dir, '../templates/')
loader = jinja2.FileSystemLoader(templates_dir)
environment = jinja2.Environment(loader=loader)

# Create /tmp/elixir-errors if not existing yet (could happen after a reboot)
errdir = '/tmp/elixir-errors'

if not(os.path.isdir(errdir)):
    os.makedirs(errdir, exist_ok=True)

# Enable CGI Trackback Manager for debugging (https://docs.python.org/fr/3/library/cgitb.html)
cgitb.enable(display=0, logdir=errdir, format='text')


# Returns a Query class instance or None if project data directory does not exist
# basedir: absolute path to parent directory of all project data directories, ex. "/srv/elixir-data/"
# project: name of the project, directory in basedir, ex. "linux"
def get_query(basedir, project):
    datadir = basedir + '/' + project + '/data'
    repodir = basedir + '/' + project + '/repo'

    if not(os.path.exists(datadir)) or not(os.path.exists(repodir)):
        return None

    return Query(datadir, repodir)

def get_error_page(basedir, title, details=None):
    template_ctx = {
        'projects': get_projects(basedir),
        'topbar_families': TOPBAR_FAMILIES,

        'error_title': title,
    }

    if details is not None:
        template_ctx['error_details'] = details

    template = environment.get_template('error.html')
    return template.render(template_ctx)

# Represents a parsed `source` URL path
# project: name of the project, ex: "musl"
# version: tagged commit of the project, ex: "v1.2.5"
# path: path to the requested file, starts with a slash, ex: "/src/prng/lrand48.c"
ParsedSourcePath = namedtuple('ParsedSourcePath', 'project, version, path')

# Parse `source` route URL path into parts
# NOTE: All parts are unquoted
def parse_source_path(path):
    m = search('^/([^/]*)/([^/]*)/[^/]*(.*)$', path)
    if m:
        return ParsedSourcePath(m.group(1), m.group(2), m.group(3))

# Converts ParsedSourcePath to a string with corresponding URL path
def stringify_source_path(ppath):
    path = f'/{ppath.project}/{ppath.version}/source{ppath.path}'
    return path.rstrip('/')

# Returns 301 redirect to path with trailing slashes removed if path has a trailing slash
def redirect_on_trailing_slash(path):
    if path[-1] == '/':
        return (301, path.rstrip('/'))

# Handles `source` URL, returns a response
# path: string with URL path of the request
def handle_source_url(path, _):
    basedir = os.environ['LXR_PROJ_DIR']

    status = redirect_on_trailing_slash(path)
    if status is not None:
        return status

    parsed_path = parse_source_path(path)
    if parsed_path is None:
        print("Error: failed to parse path in handle_source_url", path, file=sys.stderr)
        return (404, get_error_page(basedir, "Failed to parse path"))

    query = get_query(basedir, parsed_path.project)
    if not query:
        return (404, get_error_page(basedir, "Unknown project"))

    # Check if path contains only allowed characters
    if not search('^[A-Za-z0-9_/.,+-]*$', parsed_path.path):
        return (400, get_error_page(basedir, "Path contains characters that are not allowed."))

    if parsed_path.version == 'latest':
        new_parsed_path = parsed_path._replace(version=parse.quote(query.query('latest')))
        return (301, stringify_source_path(new_parsed_path))

    return generate_source_page(query, basedir, parsed_path)


# Represents a parsed `ident` URL path
# project: name of the project, ex: musl
# version: tagged commit of the project, ex: v1.2.5
# family: searched symbol family, replaced with C if unknown, ex: A
# ident: searched identificator, ex: fpathconf
ParsedIdentPath = namedtuple('ParsedIdentPath', 'project, version, family, ident')

# Parse `ident` route URL path into parts
# NOTE: All parts are unquoted
def parse_ident_path(path):
    m = search('^/([^/]*)/([^/]*)(?:/([^/]))?/[^/]*(.*)$', path)

    if m:
        family = str(m.group(3)).upper()
        # If identifier family extracted from the path is unknown,
        # replace it with C - the default family.
        # This also handles ident paths without a family,
        # ex: https://elixir.bootlin.com/linux/v6.10/ident/ROOT_DEV
        if not validFamily(family):
            family = 'C'

        parsed_path = ParsedIdentPath(
            m.group(1),
            m.group(2),
            family,
            m.group(4)[1:]
        )

        return parsed_path

# Converts ParsedIdentPath to a string with corresponding URL path
def stringify_ident_path(ppath):
    path = f'/{ppath.project}/{ppath.version}/{ppath.family}/ident/{ppath.ident}'
    return path.rstrip('/')

# Handles `ident` URL post request, returns a permanent redirect to ident/$ident_name
# parsed_path: ParsedIdentPath
# form: cgi.FieldStorage with parsed POST request form
def handle_ident_post_form(parsed_path, form):
    post_ident = form.getvalue('i')
    post_family = str(form.getvalue('f')).upper()

    if parsed_path.ident == '' and post_ident:
        post_ident = parse.quote(post_ident.strip(), safe='/')
        new_parsed_path = parsed_path._replace(
            family=post_family,
            ident=post_ident
        )
        return (302, stringify_ident_path(new_parsed_path))

# Handles `ident` URL, returns a response
# path: string with URL path
# params: cgi.FieldStorage with request parameters
def handle_ident_url(path, params):
    basedir = os.environ['LXR_PROJ_DIR']

    parsed_path = parse_ident_path(path)
    if parsed_path is None:
        print("Error: failed to parse path in handle_ident_url", path, file=sys.stderr)
        return (404, get_error_page(basedir, "Invalid path."))

    status = handle_ident_post_form(parsed_path, params)
    if status is not None:
        return status

    query = get_query(basedir, parsed_path.project)
    if not query:
        return (404, get_error_page(basedir, "Unknown project."))

    # Check if identifier contains only allowed characters
    if not parsed_path.ident or not search('^[A-Za-z0-9_\$\.%-]*$', parsed_path.ident):
        return (400, get_error_page(basedir, "Identifier is invalid."))

    if parsed_path.version == 'latest':
        new_parsed_path = parsed_path._replace(version=parse.quote(query.query('latest')))
        return (301, stringify_ident_path(new_parsed_path))

    return generate_ident_page(query, basedir, parsed_path)


# Calls proper handler functions based on URL path, returns 404 if path is unknown
# path: path part of the URL
# params: cgi.FieldStorage with request parameters
def route(path, params):
    if search('^/[^/]*/[^/]*/source.*$', path) is not None:
        return handle_source_url(path, params)
    elif search('^/[^/]*/[^/]*(?:/[^/])?/ident.*$', path) is not None:
        return handle_ident_url(path, params)
    else:
        return (404, get_error_page(os.environ['LXR_PROJ_DIR'], "Unknown path."))


TOPBAR_FAMILIES = {
    'A': 'All symbols',
    'C': 'C/CPP/ASM',
    'K': 'Kconfig',
    'D': 'Devicetree',
    'B': 'DT compatible',
}

# Returns a list of names of top-level directories in basedir
def get_directories(basedir):
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
def get_projects(basedir):
    return [ProjectEntry(p, f"/{p}/latest/source") for p in get_directories(basedir)]

# Tuple of version name and URL to chosen resource with that version
# Used to render version list in the sidebar
VersionEntry = namedtuple('VersionEntry', 'version, url')

# Takes result of Query.query('version') and prepares it for the sidebar template
# versions: OrderedDict with major parts of versions as keys, values are OrderedDicts
#   with minor version parts as keys and complete version strings as values
# get_url: function that takes a version string and returns the URL
#   for that version. Meaning of the URL can depend on the context
def get_versions(versions, get_url):
    result = OrderedDict()
    for major, minor_verions in versions.items():
        for minor, patch_versions in minor_verions.items():
            for v in patch_versions:
                if major not in result:
                    result[major] = OrderedDict()
                if minor not in result[major]:
                    result[major][minor] = []
                result[major][minor].append(VersionEntry(v, get_url(v)))

    return result

# Retruns template context used by the layout template
# q: Query object
# base: directory with project
# get_url_with_new_version: see get_url parameter of get_versions
# project: name of the project
# version: version of the project
def get_layout_template_context(q, basedir, get_url_with_new_version, project, version):
    return {
        'projects': get_projects(basedir),
        'versions': get_versions(q.query('versions'), get_url_with_new_version),
        'topbar_families': TOPBAR_FAMILIES,

        'source_base_url': f'/{ project }/{ version }/source',
        'ident_base_url': f'/{ project }/{ version }/ident',
        'current_project': project,
        'current_tag': parse.unquote(version),
        'current_family': 'A',
    }

# Guesses file format based on filename, returns code formatted as HTML
def format_code(filename, code):
    import pygments
    import pygments.lexers
    import pygments.formatters

    try:
        lexer = pygments.lexers.guess_lexer_for_filename(filename, code)
    except pygments.util.ClassNotFound:
        lexer = pygments.lexers.get_lexer_by_name('text')

    lexer.stripnl = False
    formatter = pygments.formatters.HtmlFormatter(linenos=True, anchorlinenos=True)
    return pygments.highlight(code, lexer, formatter)

# Generate formatted HTML of a file, apply filters (for ex. to add identifier links)
# q: Query object
# project: name of the requested project
# version: requested version of the project
# path: path to the file in the repository
def generate_source(q, project, version, path):
    version_unquoted = parse.unquote(version)
    code = q.query('file', version_unquoted, path)

    _, fname = os.path.split(path)
    _, extension = os.path.splitext(fname)
    extension = extension[1:].lower()
    family = q.query('family', fname)

    source_base_url = f'/{ project }/{ version }/source'

    def get_ident_url(ident, ident_family=None):
        if ident_family is None:
            ident_family = family
        ident = parse.quote(ident, safe='')
        return f'/{ project }/{ version }/{ ident_family }/ident/{ ident }'

    filter_ctx = FilterContext(
        q,
        version_unquoted,
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
    html_code_block = sub('href="#-(\d+)', 'name="L\\1" id="L\\1" href="#L\\1', html_code_block)

    for f in filters:
        html_code_block = f.untransform_formatted_code(filter_ctx, html_code_block)

    return html_code_block


# Represents a file entry in git tree
# type: either tree (directory), blob (file) or symlink
# name: filename of the file
# path: path of the file, path to the target in case of symlinks
# url: absolute URL of the file
# size: int, file size in bytes, None for directories and symlinks
DirectoryEntry = namedtuple('DirectoryEntry', 'type, name, path, url, size')

# Returns a list of DirectoryEntry objects with information about files in a directory
# q: Query object
# base_url: file URLs will be created by appending file path to this URL. It shouldn't end with a slash
# tag: requested repository tag
# path: path to the directory in the repository
def get_directory_entries(q, base_url, tag, path):
    dir_entries = []
    lines = q.query('dir', tag, path)

    for l in lines:
        type, name, size, perm = l.split(' ')
        file_path = f"{ path }/{ name }"

        if type == 'tree':
            dir_entries.append(('tree', name, file_path, f"{ base_url }{ file_path }", None))
        elif type == 'blob':
            # 120000 permission means it's a symlink
            if perm == '120000':
                dir_path = path if path.endswith('/') else path + '/'
                link_contents = q.get_file_raw(tag, file_path)
                link_target_path = os.path.abspath(dir_path + link_contents)

                dir_entries.append(('symlink', name, link_target_path, f"{ base_url }{ link_target_path }", size))
            else:
                dir_entries.append(('blob', name, file_path, f"{ base_url }{ file_path }", size))

    return dir_entries

# Generates response (status code and optionally HTML) of the `source` route
# q: Query object
# basedir: path to data directory, ex: "/srv/elixir-data"
# parsed_path: ParsedSourcePath
def generate_source_page(q, basedir, parsed_path):
    status = 200

    project = parsed_path.project
    version = parsed_path.version
    path = parsed_path.path
    version_unquoted = parse.unquote(version)
    source_base_url = f'/{ project }/{ version }/source'

    type = q.query('type', version_unquoted, path)

    if type == 'tree':
        back_path = os.path.dirname(path[:-1])
        if back_path == '/':
            back_path = ''

        template_ctx = {
            'dir_entries': get_directory_entries(q, source_base_url, version_unquoted, path),
            'back_url': f'{ source_base_url }{ back_path }' if path != '' else None,
        }
        template = environment.get_template('tree.html')
    elif type == 'blob':
        template_ctx = {
            'code': generate_source(q, project, version, path),
        }
        template = environment.get_template('source.html')
    else:
        status = 404
        template_ctx = {
            'error_title': 'This file does not exist.',
        }
        template = environment.get_template('error.html')


    # Generate breadcrumbs
    path_split = path.split('/')[1:]
    path_temp = ''
    breadcrumb_links = []
    for p in path_split:
        path_temp += '/'+p
        breadcrumb_links.append((p, f'{ source_base_url }{ path_temp }'))

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

    get_url_with_new_version = lambda v: stringify_source_path(parsed_path._replace(version=parse.quote(v, safe='')))

    # Create template context
    data = {
        **get_layout_template_context(q, basedir, get_url_with_new_version, project, version),

        'title_path': title_path,
        'breadcrumb_links': breadcrumb_links,

        **template_ctx,
    }

    return (status, template.render(data))

# Represents line in a file with URL to that line
LineWithURL = namedtuple('LineWithURL', 'lineno, url')

# Represents a symbol occurrence to be rendered by ident template
# type: type of the symbol
# path: path of the file that contains the symbol
# line: list of LineWithURL
SymbolEntry = namedtuple('SymbolEntry', 'type, path, lines')

# Converts SymbolInstance into SymbolEntry
# path of SymbolInstance will be appended to base_url
def symbol_instance_to_entry(base_url, symbol):
    # TODO this should be a responsibility of Query
    if type(symbol.line) is str:
        line_numbers = symbol.line.split(',')
    else:
        line_numbers = [symbol.line]

    lines = [
        LineWithURL(l, f'{ base_url }/{ symbol.path }#L{ l }')
        for l in line_numbers
    ]

    return SymbolEntry(symbol.type, symbol.path, lines)

# Generates response (status code and optionally HTML) of the `ident` route
# q: Query object
# basedir: path to data directory, ex: "/srv/elixir-data"
# parsed_path: ParsedIdentPath
def generate_ident_page(q, basedir, parsed_path):
    status = 200

    ident = parsed_path.ident
    version = parsed_path.version
    version_unquoted = parse.unquote(version)
    family = parsed_path.family
    project = parsed_path.project
    source_base_url = f'/{ project }/{ version }/source'

    ident_unquoted = parse.unquote(ident)
    symbol_definitions, symbol_references, symbol_doccomments = q.query('ident', version_unquoted, ident_unquoted, family)

    symbol_sections = []

    if len(symbol_definitions) or len(symbol_references):
        if len(symbol_definitions):
            defs_by_type = OrderedDict({})

            # TODO this should be a responsibility of Query
            for sym in symbol_definitions:
                if sym.type not in defs_by_type:
                    defs_by_type[sym.type] = [symbol_instance_to_entry(source_base_url, sym)]
                else:
                    defs_by_type[sym.type].append(symbol_instance_to_entry(source_base_url, sym))

            symbol_sections.append({
                'title': 'Defined',
                'symbols': defs_by_type,
            })
        else:
            symbol_sections.append({
                'message': 'No definitions found in the database',
            })

        if len(symbol_doccomments):
            symbol_sections.append({
                'title': 'Documented',
                'symbols': {'_unknown': [symbol_instance_to_entry(source_base_url, sym) for sym in symbol_doccomments]},
            })

        if len(symbol_references):
            symbol_sections.append({
                'title': 'Referenced',
                'symbols': {'_unknown': [symbol_instance_to_entry(source_base_url, sym) for sym in symbol_references]},
            })
        else:
            symbol_sections.append({
                'message': 'No references found in the database',
            })

    else:
        if ident != '':
            status = 404

    get_url_with_new_version = lambda v: stringify_ident_path(parsed_path._replace(version=parse.quote(v, safe='')))

    data = {
        **get_layout_template_context(q, basedir, get_url_with_new_version, project, version),

        'searched_ident': ident_unquoted,
        'current_family': family,

        'symbol_sections': symbol_sections,
    }

    template = environment.get_template('ident.html')
    return (status, template.render(data))

path = os.environ.get('REQUEST_URI') or os.environ.get('SCRIPT_URL')

# parses and stores request parameters, both query string and POST request form
request_params = cgi.FieldStorage()

result = route(path, request_params)

if result is not None:
    if result[0] == 200:
        print('Content-Type: text/html;charset=utf-8\n')
        print(result[1], end='')
    elif result[0] == 301:
        print('Status: 301 Moved Permanently')
        print('Location: '+ result[1] +'\n')
    elif result[0] == 302:
        print('Status: 302 Found')
        print('Location: '+ result[1] +'\n')
    elif result[0] == 400:
        print('Status: 400 Bad Request')
        print('Content-Type: text/html;charset=utf-8\n')
        print(result[1], end='')
    elif result[0] == 404:
        print('Status: 404 Not Found')
        print('Content-Type: text/html;charset=utf-8\n')
        print(result[1], end='')
    else:
        print('Status: 500 Internal Server Error')
        print('Content-Type: text/html;charset=utf-8\n')
        print('Error - route returned an unknown status code', result, file=sys.stderr)
        print('Unknown error - check error logs for details\n')
else:
    print('Status: 500 Internal Server Error')
    print('Content-Type: text/html;charset=utf-8\n')
    print('Error - route returned None', file=sys.stderr)
    print('Unknown error - check error logs for details\n')

