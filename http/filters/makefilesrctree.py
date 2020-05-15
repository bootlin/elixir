# Filters for files listed in Makefiles using $(srctree)

makefilesrctree = []

def keep_makefilesrctree(m):
    if query('exist', tag, '/' +  m.group(1)):
        makefilesrctree.append(m.group(1))
        return '__KEEPMAKEFILESRCTREE__' + encode_number(len(makefilesrctree)) + m.group(2)
    else:
        return m.group(0)

def replace_makefilesrctree(m):
    w = makefilesrctree[decode_number(m.group(1)) - 1]
    return '<a href="'+version+'/source'+'/'+w+'">'+'$(srctree)/'+w+'</a>'

makefilesrctree_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '(?:(?<=\s|=)|(?<=-I))(?!/)\$\(srctree\)/((?:[-\w/]+/)?[-\w\.]+)(\s+|\)|$)',
                'prefunc': keep_makefilesrctree,
                'postrex': '__KEEPMAKEFILESRCTREE__([A-J]+)',
                'postfunc': replace_makefilesrctree
                }

filters.append(makefilesrctree_filters)
