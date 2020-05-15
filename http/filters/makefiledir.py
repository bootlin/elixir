# Filters for Makefile directory includes as follows:
# obj-$(VALUE) += dir/

makefiledir = []

def keep_makefiledir(m):
    dir_name = os.path.dirname(path)

    if dir_name != '/':
        dir_name += '/'

    if query('exist', tag, dir_name + m.group(1) + '/Makefile'):
        makefiledir.append(m.group(1))
        return '__KEEPMAKEFILEDIR__' + encode_number(len(makefiledir)) + '/' + m.group(2)
    else:
        return m.group(0)

def replace_makefiledir(m):
    w = makefiledir[decode_number(m.group(1)) - 1]
    dir_name = os.path.dirname(path)
    
    if dir_name != '/':
        dir_name += '/'

    return '<a href="'+version+'/source'+dir_name+w+'/Makefile">'+w+'/</a>'

makefiledir_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '(?<=\s)([-\w/]+)/(\s+|$)',
                'prefunc': keep_makefiledir,
                'postrex': '__KEEPMAKEFILEDIR__([A-J]+)/',
                'postfunc': replace_makefiledir
                }

filters.append(makefiledir_filters)
