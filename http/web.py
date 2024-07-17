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

# prepare a default globals dict to be later used for filter context
default_globals = {
    **globals(),
}

import cgi
import cgitb
import os
import re
import sys
from collections import OrderedDict, namedtuple
from io import StringIO
from re import search, sub
from urllib import parse
import jinja2

sys.path = [ sys.path[0] + '/..' ] + sys.path
from lib import validFamily
from query import Query, SymbolInstance

realprint = print
outputBuffer = StringIO()

def print(arg, end='\n'):
    global outputBuffer
    outputBuffer.write(arg + end)

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
    status = redirect_on_trailing_slash(path)
    if status is not None:
        return status

    parsed_path = parse_source_path(path)
    if parsed_path is None:
        realprint("Error: failed to parse path in handle_source_url", path, file=sys.stderr)
        return (404, "Failed to parse path")

    query = get_query(os.environ['LXR_PROJ_DIR'], parsed_path.project)
    if not query:
        return (404, "Unknown project")

    # Check if path contains only allowed characters
    if not search('^[A-Za-z0-9_/.,+-]*$', parsed_path.path):
        return (400, "Path contains characters that are not allowed.")

    if parsed_path.version == 'latest':
        new_parsed_path = parsed_path._replace(version=parse.quote(query.query('latest')))
        return (301, stringify_source_path(new_parsed_path))

    return generate_source_page(query, os.environ['LXR_PROJ_DIR'], parsed_path)


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
    parsed_path = parse_ident_path(path)
    if parsed_path is None:
        realprint("Error: failed to parse path in handle_ident_url", path, file=sys.stderr)
        return (404, "Failed to parse path")

    status = handle_ident_post_form(parsed_path, params)
    if status is not None:
        return status

    query = get_query(os.environ['LXR_PROJ_DIR'], parsed_path.project)
    if not query:
        return (404, "Unknown project")

    # Check if identifier contains only allowed characters
    if not parsed_path.ident or not search('^[A-Za-z0-9_\$\.%-]*$', parsed_path.ident):
        return (400, "Identifier contains characters that are not allowed.")

    if parsed_path.version == 'latest':
        new_parsed_path = parsed_path._replace(version=parse.quote(query.query('latest')))
        return (301, stringify_ident_path(new_parsed_path))

    return generate_ident_page(query, os.environ['LXR_PROJ_DIR'], parsed_path)


# Calls proper handler functions based on URL path, returns 404 if path is unknown
# path: path part of the URL
# params: cgi.FieldStorage with request parameters
def route(path, params):
    if search('^/[^/]*/[^/]*/source.*$', path) is not None:
        return handle_source_url(path, params)
    elif search('^/[^/]*/[^/]*(?:/[^/])?/ident.*$', path) is not None:
        return handle_ident_url(path, params)
    else:
        return (404, "Unknown path")


# Returns a list of names of top-level directories in basedir
def get_directories(basedir):
    directories = []
    for filename in os.listdir(basedir):
        filepath = os.path.join(basedir, filename)
        if os.path.isdir(filepath):
            directories.append(filename)
    return sorted(directories)

def generate_source(q, code, path, version, tag, project):
    import pygments
    import pygments.lexers
    import pygments.formatters

    fdir, fname = os.path.split(path)
    filename, extension = os.path.splitext(fname)
    extension = extension[1:].lower()
    family = q.query('family', fname)

    # globals required by filters
    # this dict is also modified by filters - most introduce new, global variables 
    # that are later used by prefunc/postfunc
    filter_ctx = {
        **default_globals,
        "os": os,
        "parse": parse,
        "re": re,
        "dts_comp_support": q.query('dts-comp'),

        "version": version,
        "family": family,
        "path": path,
        "tag": tag,
        "q": q,
    }

    # Source common filter definitions
    os.chdir('filters')
    exec(open("common.py").read(), filter_ctx)

    # Source project specific filters
    f = project + '.py'
    if os.path.isfile(f):
        exec(open(f).read(), filter_ctx)
    os.chdir('..')

    filters = filter_ctx["filters"]

    # Apply filters
    for f in filters:
        c = f['case']
        if (c == 'any' or
            (c == 'filename' and filename in f['match']) or
            (c == 'extension' and extension in f['match']) or
            (c == 'path' and fdir.startswith(tuple(f['match']))) or
            (c == 'filename_extension' and filename.endswith(tuple(f['match'])))):

            apply_filter = True

            if 'path_exceptions' in f:
                for p in f['path_exceptions']:
                    if re.match(p, path):
                        apply_filter = False
                        break

            if apply_filter:
                code = sub(f ['prerex'], f ['prefunc'], code, flags=re.MULTILINE)


    try:
        lexer = pygments.lexers.guess_lexer_for_filename(path, code)
    except:
        lexer = pygments.lexers.get_lexer_by_name('text')

    lexer.stripnl = False
    formatter = pygments.formatters.HtmlFormatter(linenos=True, anchorlinenos=True)
    result = pygments.highlight(code, lexer, formatter)

    # Replace line numbers by links to the corresponding line in the current file
    result = sub('href="#-(\d+)', 'name="L\\1" id="L\\1" href="'+version+'/source'+path+'#L\\1', result)

    for f in filters:
        c = f['case']
        if (c == 'any' or
            (c == 'filename' and filename in f['match']) or
            (c == 'extension' and extension in f['match']) or
            (c == 'path' and fdir.startswith(tuple(f['match']))) or
            (c == 'filename_extension' and filename.endswith(tuple(f['match'])))):

            result = sub(f ['postrex'], f ['postfunc'], result)

    return result

# Generates response (status code and optionally HTML) of the `source` route
# q: Query object
# basedir: path to data directory, ex: "/srv/elixir-data"
# parsed_path: ParsedSourcePath
def generate_source_page(q, basedir, parsed_path):
    status = 200

    url = 'source' + parsed_path.path
    project = parsed_path.project
    version = parsed_path.version
    path = parsed_path.path
    tag = parse.unquote(version)

    lines = []

    type = q.query('type', tag, path)
    if len(type) > 0:
        if type == 'tree':
            lines += q.query('dir', tag, path)
        elif type == 'blob':
            code = q.query('file', tag, path)
    else:
        template_ctx = {
            'error_title': 'This file does not exist.',
        }
        template = environment.get_template('error.html')
        status = 404

    if type == 'tree':
        dir_entries = []

        if path != '':
            back_path = os.path.dirname(path[:-1])
            if back_path == '/':
                back_path = ''
            dir_entries.append(('back', 'Parent directory', back_path, ''))

        for l in lines:
            type, name, size, perm = l.split(' ')

            if type == 'tree':
                dir_entries.append(('tree', name, f"{path}/{name}", ''))
            if type == 'blob':
                file_path = f"{path}/{name}"

                # 120000 permission means it's a symlink
                if perm == '120000':
                    dir_name = os.path.dirname(path)
                    rel_path = q.query('file', tag, file_path)

                    if dir_name != '/':
                        dir_name += '/'

                    file_path = os.path.abspath(dir_name + rel_path)
                    name = name + ' -> ' + file_path

                dir_entries.append(('blob', name, file_path, f"{size} bytes"))

        template_ctx = {
            'dir_entries': dir_entries,
        }
        template = environment.get_template('tree.html')

    elif type == 'blob':
        template_ctx = {
            'code': generate_source(q, code, path, version, tag, project),
        }
        template = environment.get_template('source.html')

    # Generate breadcrumbs
    path_split = path.split('/')[1:]
    path_temp = ''
    breadcrumb_links = []
    for p in path_split:
        path_temp += '/'+p
        breadcrumb_links.append((p, version + '/source' + path_temp))

    # Generate title
    title_suffix = project.capitalize()+' source code ('+tag+') - Bootlin'

    # Create titles like this:
    # root path: "Linux source code (v5.5.6) - Bootlin"
    # first level path: "arch - Linux source code (v5.5.6) - Bootlin"
    # deeper paths: "Makefile - arch/um/Makefile - Linux source code (v5.5.6) - Bootlin"
    title = ('' if path == ''
                     else path_split[0]+' - ' if len(path_split) == 1
                     else path_split[-1]+' - '+'/'.join(path_split)+' - ') \
            +title_suffix

    # Create template context
    data = {
        **template_ctx,

        'baseurl': '/' + project + '/',
        'tag': tag,
        'version': version,
        'url': url,
        'project': project,
        'projects': get_directories(basedir),
        'ident': '',
        'family': 'A',

        'breadcrumb_links': breadcrumb_links,
        'title': title,

        'versions': q.query('versions'),
        'url': url,
        'current_tag': tag,
    }

    return (status, template.render(data))


# TODO this should be a responsibility of Query
def convert_symbol_lines(symbol):
    if type(symbol.line) is str:
        return SymbolInstance(symbol.path, symbol.line.split(','), symbol.type)
    else:
        return SymbolInstance(symbol.path, [str(symbol.line)], symbol.type)

# Generates response (status code and optionally HTML) of the `ident` route
# q: Query object
# basedir: path to data directory, ex: "/srv/elixir-data"
# parsed_path: ParsedIdentPath
def generate_ident_page(q, basedir, parsed_path):
    status = 200

    ident = parsed_path.ident
    url = parsed_path.family + '/ident/' + ident
    version = parsed_path.version
    tag = parse.unquote(version)
    family = parsed_path.family

    symbol_definitions, symbol_references, symbol_doccomments = q.query('ident', tag, ident, family)

    symbol_sections = []

    if len(symbol_definitions) or len(symbol_references):
        if len(symbol_definitions):
            defs_by_type = OrderedDict({})

            # TODO this should be a responsibility of Query
            for symbol_definition in symbol_definitions:
                if symbol_definition.type in defs_by_type:
                    defs_by_type[symbol_definition.type].append(convert_symbol_lines(symbol_definition))
                else:
                    defs_by_type[symbol_definition.type] = [convert_symbol_lines(symbol_definition)]

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
                'symbols': {'_unknown': [convert_symbol_lines(sym) for sym in symbol_doccomments]},
            })

        if len(symbol_references):
            symbol_sections.append({
                'title': 'Referenced',
                'symbols': {'_unknown': [convert_symbol_lines(sym) for sym in symbol_references]},
            })
        else:
            symbol_sections.append({
                'message': 'No references found in the database',
            })

    else:
        if ident != '':
            status = 404

    # Create template context
    project = parsed_path.project

    title_suffix = project.capitalize()+' source code ('+tag+') - Bootlin'

    data = {
        'baseurl': '/' + project + '/',
        'tag': tag,
        'version': version,
        'url': url,
        'project': project,
        'projects': get_directories(basedir),
        'ident': ident,
        'family': family,

        'title': ident+' identifier - '+title_suffix,

        'versions': q.query('versions'),
        'url': url,
        'current_tag': tag,

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
        realprint('Content-Type: text/html;charset=utf-8\n')
        realprint(result[1], end='')
    elif result[0] == 301:
        realprint('Status: 301 Moved Permanently')
        realprint('Location: '+ result[1] +'\n')
        exit()
    elif result[0] == 302:
        realprint('Status: 302 Found')
        realprint('Location: '+ result[1] +'\n')
        exit()
    elif result[0] == 400:
        realprint('Status: 400 Bad Request\n')
        exit()
    elif result[0] == 404:
        realprint('Status: 404 Not Found')
        realprint('Content-Type: text/html;charset=utf-8\n')
        realprint(result[1], end='')
    else:
        realprint('Status: 500 Internal Server Error')
        realprint('Content-Type: text/html;charset=utf-8\n')
        realprint('Error - route returned an unknown status code', result, file=sys.stderr)
        realprint('Unknown error - check error logs for details\n')
else:
    realprint('Status: 500 Internal Server Error')
    realprint('Content-Type: text/html;charset=utf-8\n')
    realprint('Error - route returned None', file=sys.stderr)
    realprint('Unknown error - check error logs for details\n')

