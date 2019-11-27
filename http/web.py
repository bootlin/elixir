#!/usr/bin/python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017  Mikaël Bouillot
#  <mikael.bouillot@bootlin.com>
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

from io import StringIO
from urllib import parse

realprint = print
outputBuffer = StringIO()

def print (arg, end='\n'):
    global outputBuffer
    outputBuffer.write (arg + end)

# Enable CGI Trackback Manager for debugging (https://docs.python.org/fr/3/library/cgitb.html)
import cgitb
cgitb.enable()

import cgi
import os
import re
from re import search, sub

ident = ''
status = 200

# Split the URL into its components (project, version, cmd, arg)
m = search ('^/([^/]*)/([^/]*)/([^/]*)(.*)$', os.environ['SCRIPT_URL'])

if m:
    project = m.group (1)
    version = m.group (2)
    cmd = m.group (3)
    arg = m.group (4)
    if not (project and search ('^[A-Za-z0-9-]+$', project)) \
    or not (version and search ('^[A-Za-z0-9._-]+$', version)):
        status = 302
        location = '/linux/latest/'+cmd+arg
        cmd = ''
    if cmd == 'source':
        path = arg
        if len (path) > 0 and path[-1] == '/':
            path = path[:-1]
            status = 301
            location = '/'+project+'/'+version+'/source'+path
        else:
            mode = 'source'
            if not search ('^[A-Za-z0-9_/.,+-]*$', path):
                path = 'INVALID'
            url = 'source'+path
    elif cmd == 'ident':
        ident = arg[1:]
        form = cgi.FieldStorage()
        ident2 = form.getvalue ('i')
        if ident == '' and ident2:
            status = 302
            ident2 = parse.quote(ident2.strip())
            location = '/'+project+'/'+version+'/ident/'+ident2
        else:
            mode = 'ident'
            if not (ident and search ('^[A-Za-z0-9_-]*$', ident)):
                ident = ''
            url = 'ident/'+ident
else:
    status = 404

if status == 301:
    realprint ('Status: 301 Moved Permanently')
    realprint ('Location: '+location+'\n')
    exit()
elif status == 302:
    realprint ('Status: 302 Found')
    realprint ('Location: '+location+'\n')
    exit()
elif status == 404:
    realprint ('Status: 404 Not Found\n')
    exit()

basedir = os.environ['LXR_PROJ_DIR']
os.environ['LXR_DATA_DIR'] = basedir + '/' + project + '/data';
os.environ['LXR_REPO_DIR'] = basedir + '/' + project + '/repo';

projects = []
for (dirpath, dirnames, filenames) in os.walk (basedir):
    projects.extend (dirnames)
    break
projects.sort ()

import sys
sys.path = [ sys.path[0] + '/..' ] + sys.path
import query

def call_query(*args):
    cwd = os.getcwd()
    os.chdir ('..')
    ret = query.query (*args)
    os.chdir (cwd)

    return ret

if version == 'latest':
    tag = call_query ('latest')
else:
    tag = version

data = {
    'baseurl': '/' + project + '/',
    'tag': tag,
    'version': version,
    'url': url,
    'project': project,
    'projects': projects,
    'ident': ident,
    'breadcrumb': '<a class="project" href="'+version+'/source">/</a>'
}

versions = call_query ('versions')

v = ''
b = 1
for topmenu in versions:
    submenus = versions[topmenu]
    v += '<li>\n'
    v += '\t<span>'+topmenu+'</span>\n'
    v += '\t<ul>\n'
    b += 1
    for submenu in submenus:
        tags = submenus[submenu]
        if submenu == tags[0] and len(tags) == 1:
            if submenu == tag: v += '\t\t<li class="li-link active"><a href="'+submenu+'/'+url+'">'+submenu+'</a></li>\n'
            else: v += '\t\t<li class="li-link"><a href="'+submenu+'/'+url+'">'+submenu+'</a></li>\n'
        else:
            v += '\t\t<li>\n'
            v += '\t\t\t<span>'+submenu+'</span>\n'
            v += '\t\t\t<ul>\n'
            for _tag in tags:
                if _tag == tag: v += '\t\t\t\t<li class="li-link active"><a href="'+_tag+'/'+url+'">'+_tag+'</a></li>\n'
                else: v += '\t\t\t\t<li class="li-link"><a href="'+_tag+'/'+url+'">'+_tag+'</a></li>\n'
            v += '\t\t\t</ul></li>\n'
    v += '\t</ul></li>\n'

data['versions'] = v

if mode == 'source':
    p2 = ''
    p3 = path.split ('/') [1:]
    links = []
    for p in p3:
        p2 += '/'+p
        links.append ('<a href="'+version+'/source'+p2+'">'+p+'</a>')

    if links:
        data['breadcrumb'] += '/'.join (links)

    data['ident'] = ident
    data['title'] = project.capitalize ()+' source code: '+path[1:]+' ('+tag+') - Bootlin'

    lines = ['null - -']

    type = call_query ('type', tag, path)
    if len (type) > 0:
        if type == 'tree':
            lines += call_query ('dir', tag, path)
        elif type == 'blob':
            blob_content = call_query ('file', tag, path)
            lines += blob_content.split("\n")[:-1]
    else:
        print ('<div class="lxrerror"><h2>This file does not exist.</h2></div>')
        status = 404

    if type == 'tree':
        if path != '':
            lines[0] = 'back - -'

        print ('<div class="lxrtree">')
        print ('<table><tbody>\n')
        for l in lines:
            type, name, size = l.split (' ')

            if type == 'null':
                continue
            elif type == 'tree':
                size = ''
                path2 = path+'/'+name
                name = name
            elif type == 'blob':
                size = size+' bytes'
                path2 = path+'/'+name
            elif type == 'back':
                size = ''
                path2 = os.path.dirname (path[:-1])
                if path2 == '/': path2 = ''
                name = 'Parent directory'

            print ('  <tr>\n')
            print ('    <td><a class="tree-icon icon-'+type+'" href="'+version+'/source'+path2+'">'+name+'</a></td>\n')
            print ('    <td><a tabindex="-1" class="size" href="'+version+'/source'+path2+'">'+size+'</a></td>\n')
            print ('  </tr>\n')

        print ('</tbody></table>', end='')
        print ('</div>')

    elif type == 'blob':
        del (lines[0])

        import pygments
        import pygments.lexers
        import pygments.formatters

        links = []
        dtsi = []
        code = StringIO()
        kconfig = []

        filename, extension = os.path.splitext(path)
        extension = extension[1:].lower()
        filename = os.path.basename(filename)

        def keep_links(match):
            links.append (match.group (1))
            return '__KEEPLINKS__' + str(len(links))

        def replace_links(match):
            i = links[int (match.group (1)) - 1]
            return '<a href="'+version+'/ident/'+i+'">'+i+'</a>'

        def keep_dtsi(match):
            dtsi.append (match.group (4))
            return match.group (1) + match.group (2) + match.group (3) + '"__KEEPDTSI__' + str(len(dtsi)) + '"'

        def replace_dtsi(match):
            w = dtsi[int (match.group (1)) - 1]
            return '<a href="'+version+'/source'+os.path.dirname(path)+'/'+w+'">'+w+'</a>'

        def keep_kconfig(match):
            kconfig.append (match.group (4))
            return match.group (1) + match.group (2) + match.group (3) + '"__KEEPKCONFIG__' + str(len(kconfig)) + '"'

        def replace_kconfig(match):
            w = kconfig[int (match.group (1)) - 1]
            return '<a href="'+version+'/source/'+w+'">'+w+'</a>'

        for l in lines:
	    # Protect identifiers, to be able to replace them in the pygments output (replace_links function)
            l = sub ('\033\[31m(.*?)\033\[0m', keep_links, l)
            code.write (l + '\n')

        code = code.getvalue()

        if extension in {'dts', 'dtsi'}:
            code = sub ('^(\s*)(#include|/include/)(\s*)\"(.*?)\"', keep_dtsi, code, flags=re.MULTILINE)

        if filename in {'Kconfig'}:
            code = sub ('^(\s*)(source)(\s*)\"(.*?)\"', keep_kconfig, code, flags=re.MULTILINE)

        try:
            lexer = pygments.lexers.guess_lexer_for_filename (path, code)
        except:
            lexer = pygments.lexers.get_lexer_by_name ('text')

        lexer.stripnl = False
        formatter = pygments.formatters.HtmlFormatter (linenos=True, anchorlinenos=True)
        result = pygments.highlight (code, lexer, formatter)

	# Replace line numbers by links to the corresponding line in the current file
        result = sub ('href="#-(\d+)', 'name="L\\1" id="L\\1" href="'+version+'/source'+path+'#L\\1', result)
	# Add the links to identifiers, using the KEEPLINKS markers
        result = sub ('__KEEPLINKS__(\d+)', replace_links, result)

        if extension in {'dts', 'dtsi'}:
            result = sub ('__KEEPDTSI__(\d+)', replace_dtsi, result)

        if filename in {'Kconfig'}:
            result = sub ('__KEEPKCONFIG__(\d+)', replace_kconfig, result)

        print ('<div class="lxrcode">' + result + '</div>')


elif mode == 'ident':
    data['title'] = project.capitalize ()+' source code: '+ident+' identifier ('+tag+') - Bootlin'

    symbol_definitions, symbol_references = call_query ('ident', tag, ident)

    print ('<div class="lxrident">')
    if len(symbol_definitions):
        print ('<h2>Defined in '+str(len(symbol_definitions))+' files:</h2>')
        print ('<ul>')
        for symbol_definition in symbol_definitions:
            print ('<li><a href="{v}/source/{f}#L{n}"><strong>{f}</strong>, line {n} <em>(as a {t})</em></a>'.format(
                v=version, f=symbol_definition.path, n=symbol_definition.line, t=symbol_definition.type
            ))
        print ('</ul>')

        print ('<h2>Referenced in '+str(len(symbol_references))+' files:</h2>')
        print ('<ul>')
        for symbol_reference in symbol_references:
            ln = symbol_reference.line.split (',')
            if len (ln) == 1:
                n = ln[0]
                print ('<li><a href="{v}/source/{f}#L{n}"><strong>{f}</strong>, line {n}</a>'.format(
                    v=version, f=symbol_reference.path, n=n
                ))
            else:
                if len(symbol_references) > 100:    # Concise display
                    n = len (ln)
                    print ('<li><a href="{v}/source/{f}"><strong>{f}</strong>, <em>{n} times</em></a>'.format(
                        v=version, f=symbol_reference.path, n=n
                    ))
                else:    # Verbose display
                    print ('<li><a href="{v}/source/{f}#L{n}"><strong>{f}</strong></a>'.format(
                        v=version, f=symbol_reference.path, n=ln[0]
                    ))
                    print ('<ul>')
                    for n in ln:
                        print ('<li><a href="{v}/source/{f}#L{n}">line {n}</a>'.format(
                            v=version, f=symbol_reference.path, n=n
                        ))
                    print ('</ul>')
        print ('</ul>')
    else:
        if ident != '':
            print ('<h2>Identifier not used</h2>')
            status = 404
    print ('</div>')

else:
    print ('Invalid request')

if status == 404:
    realprint ('Status: 404 Not Found')

import jinja2
loader = jinja2.FileSystemLoader (os.path.join (os.path.dirname (__file__), '../templates/'))
environment = jinja2.Environment (loader=loader)
template = environment.get_template ('layout.html')

realprint ('Content-Type: text/html;charset=utf-8\n')
data['main'] = outputBuffer.getvalue()
realprint (template.render(data), end='')
