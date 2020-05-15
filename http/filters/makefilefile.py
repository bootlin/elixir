# Filters for files listed in Makefiles

makefilefile = []

def keep_makefilefile(m):
    dir_name = os.path.dirname(path)

    if dir_name != '/':
        dir_name += '/'

    if query('exist', tag, dir_name + m.group(1)):
        makefilefile.append(m.group(1))
        return '__KEEPMAKEFILEFILE__' + encode_number(len(makefilefile)) + m.group(2)
    else:
        return m.group(0)

def replace_makefilefile(m):
    w = makefilefile[decode_number(m.group(1)) - 1]
    dir_name = os.path.dirname(path)
    
    if dir_name != '/':
        dir_name += '/'

    return '<a href="'+version+'/source'+dir_name+w+'">'+w+'</a>'

makefilefile_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '(?:(?<=\s|=)|(?<=-I))(?!/)([-\w/]+/[-\w\.]+)(\s+|\)|$)',
                'prefunc': keep_makefilefile,
                'postrex': '__KEEPMAKEFILEFILE__([A-J]+)',
                'postfunc': replace_makefilefile
                }

filters.append(makefilefile_filters)
