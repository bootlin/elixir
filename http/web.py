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

realprint = print
outputBuffer = StringIO()

def print (arg, end='\n'):
    global outputBuffer
    outputBuffer.write (arg + end)

# enable debugging
import cgitb
cgitb.enable()

import cgi
import os
from re import search, sub
from collections import OrderedDict

ident = ''
status = 200

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
            ident2 = ident2.strip()
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

def do_query (*args):
    cwd = os.getcwd()
    os.chdir ('..')
    a = query.query (*args)
    os.chdir (cwd)

    # decode('ascii') fails on special chars
    # FIXME: major hack until we handle everything as bytestrings
    try:
        a = a.decode ('utf-8')
    except UnicodeDecodeError:
        a = a.decode ('iso-8859-1')
    a = a.split ('\n')
    del a[-1]
    return a

if version == 'latest':
    tag = do_query ('latest')[0]
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

lines = do_query ('versions')
va = OrderedDict()
for l in lines:
    m = search ('^([^ ]*) ([^ ]*) ([^ ]*)$', l)
    if not m:
        continue
    m1 = m.group(1)
    m2 = m.group(2)
    l = m.group(3)

    if m1 not in va:
        va[m1] = OrderedDict()
    if m2 not in va[m1]:
        va[m1][m2] = []
    va[m1][m2].append (l)

v = ''
b = 1
for v1k in va:
    v1v = va[v1k]
    v += '<li>\n'
    v += '\t<span>'+v1k+'</span>\n'
    v += '\t<ul>\n'
    b += 1
    for v2k in v1v:
        v2v = v1v[v2k]
        if v2k == v2v[0] and len(v2v) == 1:
            if v2k == tag: v += '\t\t<li class="li-link active"><a href="'+v2k+'/'+url+'">'+v2k+'</a></li>\n'
            else: v += '\t\t<li class="li-link"><a href="'+v2k+'/'+url+'">'+v2k+'</a></li>\n'
        else:
            v += '\t\t<li>\n'
            v += '\t\t\t<span>'+v2k+'</span>\n'
            v += '\t\t\t<ul>\n'
            for v3 in v2v:
                if v3 == tag: v += '\t\t\t\t<li class="li-link active"><a href="'+v3+'/'+url+'">'+v3+'</a></li>\n'
                else: v += '\t\t\t\t<li class="li-link"><a href="'+v3+'/'+url+'">'+v3+'</a></li>\n'
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

    type = do_query ('type', tag, path)
    if len (type) == 1:
        type = type[0]
        if type == 'tree':
            lines += do_query ('dir', tag, path)
        elif type == 'blob':
            lines += do_query ('file', tag, path)
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
        code = StringIO()

        def keep_links(match):
            links.append (match.group (1))
            g = match.group(1)
            return '__KEEPLINKS__' + str(len(links))

        def replace_links(match):
            i = links[int (match.group (1)) - 1]
            return '<a href="'+version+'/ident/'+i+'">'+i+'</a>'

        for l in lines:
            l = sub ('\033\[31m(.*?)\033\[0m', keep_links, l)
            l = sub ('\033\[32m', '', l)
            l = sub ('\033\[33m', '', l)
            l = sub ('\033\[0m', '', l)
            code.write (l + '\n')

        code = code.getvalue()

        try:
            lexer = pygments.lexers.guess_lexer_for_filename (path, code)
        except:
            lexer = pygments.lexers.get_lexer_by_name ('text')

        formatter = pygments.formatters.HtmlFormatter (linenos=True, anchorlinenos=True)
        result = pygments.highlight (code, lexer, formatter)

        result = sub ('href="#-(\d+)', 'name="L\\1" id="L\\1" href="'+version+'/source'+path+'#L\\1', result)
        result = sub ('__KEEPLINKS__(\d+)', replace_links, result)

        print ('<div class="lxrcode">' + result + '</div>')


elif mode == 'ident':
    data['title'] = project.capitalize ()+' source code: '+ident+' identifier ('+tag+') - Bootlin'

    lines = do_query ('ident', tag, ident)
    lines = iter (lines)

    print ('<div class="lxrident">')
    m = search ('Defined in (\d*) file', next (lines))
    if m:
        num = int (m.group(1))
        if num == 0:
            status = 404

        print ('<h2>Defined in '+str(num)+' files:</h2>')
        print ('<ul>')
        for i in range (0, num):
            l = next (lines)
            m = search ('^(.*): (\d*) \((.*)\)$', l)
            f, n, t = m.groups()
            print ('<li><a href="'+version+'/source/'+f+'#L'+n+'"><strong>'+f+'</strong>, line '+n+' <em>(as a '+t+')</em></a>')
        print ('</ul>')

        next (lines)

        m = search ('Referenced in (\d*) file', next (lines))
        num = int (m.group(1))

        print ('<h2>Referenced in '+str(num)+' files:</h2>')
        print ('<ul>')
        for i in range (0, num):
            l = next (lines)
            m = search ('^(.*): (.*)$', l)
            f = m.group (1)
            ln = m.group (2).split (',')
            if len (ln) == 1:
                n = ln[0]
                print ('<li><a href="'+version+'/source/'+f+'#L'+str(n)+'"><strong>'+f+'</strong>, line '+str(n)+'</a>')
            else:
                if num > 100:    # Concise display
                    n = len (ln)
                    print ('<li><a href="'+version+'/source/'+f+'"><strong>'+f+'</strong>, <em>'+str(n)+' times</em></a>')
                else:    # Verbose display
                    print ('<li><a href="'+version+'/source/'+f+'#L'+str(ln[0])+'"><strong>'+f+'</strong></a>')
                    print ('<ul>')
                    for n in ln:
                        print ('<li><a href="'+version+'/source/'+f+'#L'+str(n)+'">line '+str(n)+'</a>')
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
