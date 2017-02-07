#!/usr/bin/python3

from subprocess import check_output

def shell_exec (cmd):
    try:
        a = check_output (cmd, shell=True)
    except:
        a = b'error\n'

    # decode('ascii') fails on special chars
    # FIXME: major hack until we handle everything as bytestrings
    try:
        a = a.decode ('utf-8')
    except UnicodeDecodeError:
        a = a.decode ('iso-8859-1')
    a = a.split ('\n')
    del a[-1]
    return a

# enable debugging
import cgitb
cgitb.enable()

import cgi
import os
from re import search, sub
from collections import OrderedDict

print ('Content-Type: text/html;charset=utf-8\n')

form = cgi.FieldStorage()
version = form.getvalue ('v')
if not (version and search ('^[A-Za-z0-9.-]+$', version)):
    version = '4.9'

url = os.environ['SCRIPT_URL']
m = search ('^/source/(.*)$', url)
if m:
    mode = 'source'
    path = m.group (1)
    if not search ('^[A-Za-z0-9_/.,+-]*$', path):
        path = 'INVALID'
    url2 = 'source/'+path+'?'

elif url == '/ident':
    mode = 'ident'
    ident = form.getvalue ('i')
    if not (ident and search ('^[A-Za-z0-9_]*$', ident)):
        ident = ''
    url2 = 'ident?i='+ident+'&'

elif url == '/search':
    mode = 'search'
    url2 = 'search?'

head = open ('template-head').read()
head = sub ('\$baseurl', 'http://' + os.environ['HTTP_HOST'], head)
head = sub ('\$vvar', version, head)

lines = shell_exec ('cd ..; ./query.py versions')
va = OrderedDict()
for l in lines:
    if search ('^2\.6', l):
        m = search ('^(2\.6)(\.[0-9]*)((\.|-).*)?$', l)
    else:
        m = search ('^([0-9]*)(\.[0-9]*)((\.|-).*)?$', l)

    m1 = m.group(1)
    m2 = m.group(2)

    if m1 not in va:
        va[m1] = OrderedDict()
    if m1+m2 not in va[m1]:
        va[m1][m1+m2] = []
    va[m1][m1+m2].append (l)

v = '<ul id="menu">\n'
b = 1
for v1k in va:
    v1v = va[v1k]
    v += ' <li class="menuitem" id="mi0'+str(b)+'"><a href="'+url2+'v='+v1k+'">v'+v1k+'</a>\n'
    b += 1
    v += ' <ul class="submenu">\n'
    for v2k in v1v:
        v2v = v1v[v2k]
        v += '  <li><a href="'+url2+'v='+v2k+'">v'+v2k+'</a>\n'
        v += '  <ul class="subsubmenu">\n'
        for v3 in v2v:
            v += '   <li><a href="'+url2+'v='+v3+'">v'+v3+'</a></li>\n'
        v += '  </ul></li>\n'
    v += ' </ul></li>\n'
v += '</ul>\n'

head = sub ('\$versions', v, head)

if mode == 'source':
    banner = '<a href="source/?v='+version+'">Linux</a>/'
    p2 = ''
    p3 = path.split ('/')
    last = p3[-1]
    p3 = p3[:-1]
    for p in p3:
        banner += '<a href="source/'+p2+p+'/?v='+version+'">'+p+'</a>/'
        p2 += p+'/'
    if last != '':
        banner += '<a href="source/'+p2+last+'?v='+version+'">'+last+'</a>'

    head = sub ('\$banner', banner, head)
    head = sub ('\$title', 'Linux/'+path+' - Linux Cross Reference - Free Electrons', head)
    print (head, end='')

    lines = ['null - -']
    
    if path[-1:] == '/' or path == '':
        type = 'tree'
        lines += shell_exec ('cd ..; ./query.py dir '+version+' \''+path+'\'')
    else:
        type = 'blob'
        lines += shell_exec ('cd ..; ./query.py file '+version+' \''+path+'\'')

    if type == 'tree':
        if path != '':
            lines[0] = 'back - -'

        print ('<table>\n')
        for l in lines:
            type, name, size = l.split (' ')

            if type == 'null':
                continue
            elif type == 'tree':
                icon = 'folder.gif'
                size = ''
                path2 = path+name+'/'
                name = name+'/'
            elif type == 'blob':
                icon = 'text.gif'
                size = size+' bytes'
                path2 = path+name
            elif type == 'back':
                icon = 'back.gif'
                size = ''
                path2 = os.path.dirname (path[:-1]) + '/'
                if path2 == '/': path2 = './'
                name = 'Parent directory'

            print ('  <tr>')
            print ('    <td><a href="source/'+path2+'?v='+version+'"><img src="/icons/'+icon+'" width="20" height="22" border="0" alt="'+icon+'"/></a></td>')
            print ('    <td><a href="source/'+path2+'?v='+version+'">'+name+'</a></td>')
            print ('    <td>'+size+'</td>')

            print ('  </tr>\n')

        print ('</table>', end='')

    elif type == 'blob':
        del (lines[0])

        print ('<div id="lxrcode"><pre>')

        width = len (str (len (lines))) 
        num = 1
        n2 = ('%'+str(width)+'d') % num
        for l in lines:
            print ('<a name="L'+str(num)+'" href="source/'+path+'?v='+version+'#L'+str(num)+'">'+n2+'</a> ', end='')
            l = cgi.escape (l)
            l = sub ('"', '&quot;', l)
            l = sub ('\033\[31m(.*?)\033\[0m', '<a href="ident?v='+version+'&i=\\1">\\1</a>', l)
            l = sub ('\033\[32m', '<i>', l)
            l = sub ('\033\[0m', '</i>', l)
            print (l)
            num += 1
            n2 = ('%'+str(width)+'d') % num

        print ('</pre></div>', end='')


elif mode == 'ident':
    field = '</h1>\n<form method="get" action="ident">\n<input type=hidden name="v" value="'+version+'">\nIdentifier: <input type="text" name="i" value="'+ident+'"size="60"/>\n<input type="submit" value="Go get it"/>\n</form>\n<h1>' + ident
    head = sub ('\$banner', field, head)
    head = sub ('\$title', 'Linux identifier search "'+ident+'" - Linux Cross Reference - Free Electrons', head)
    print (head, end='')

    lines = shell_exec ('cd .. ; ./query.py ident '+version+' '+ident)
    lines = iter (lines)

    m = search ('Defined in (\d*) file', next (lines))
    if m:
        num = int (m.group(1))

        print ('Defined in', num, 'files:')
        print ('<ul>')
        for i in range (0, num):
            l = next (lines)
            m = search ('^(.*): (\d*) \((.*)\)$', l)
            f, n, t = m.groups()
            print ('<li><a href="source/'+f+'?v='+version+'#L'+n+'">'+f+', line '+n+' (as a '+t+')</a>', end='')
        print ('</ul>')

        next (lines)

        m = search ('Referenced in (\d*) file', next (lines))
        num = int (m.group(1))

        print ('Referenced in', num, 'files:')
        print ('<ul>')
        for i in range (0, num):
            l = next (lines)
            m = search ('^(.*): (.*)$', l)
            f = m.group (1)
            ln = m.group (2).split (',')
            if len (ln) == 1:
                n = ln[0]
                print ('<li><a href="source/'+f+'?v='+version+'#L'+str(n)+'">'+f+', line '+str(n)+'</a>', end='')
            else:
                if num > 100:    # Concise display
                    n = len (ln)
                    print ('<li><a href="source/'+f+'?v='+version+'">'+f+'</a>, '+str(n)+' times')
                else:    # Verbose display
                    print ('<li>'+f)
                    print ('<ul>')
                    for n in ln:
                        print ('<li><a href="source/'+f+'?v='+version+'#L'+str(n)+'">line '+str(n)+'</a>')
                    print ('</ul>')
        print ('</ul>')
    else:
        if ident != '':
            print ('Not used')

elif mode == 'search':
    head = sub ('\$banner', '', head)
    head = sub ('\$title', 'Linux freetext search - Linux Cross Reference - Free Electrons', head)
    print (head, end='')

    print ('<form method="get" action="http://www.google.com/search"><input type="text"   name="q" size="31" maxlength="255" value="" /><input type="submit" value="Google Search" /><input type="radio"  name="sitesearch" value="" /> The Web<input type="radio"  name="sitesearch" value="lxr.free-electrons.com/source" checked="checked"/>lxr.free-electrons.com/source</form>')

else:
    print (head)
    print ('Invalid request')

print (open ('template-tail').read(), end='')

