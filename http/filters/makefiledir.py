# Filters for Makefile directory includes as follows:
# obj-$(VALUE) += dir/

makefiledir = []

def keep_makefiledir(m):
    makefiledir.append(m.group(1))
    return '__KEEPMAKEFILEDIR__' + str(len(makefiledir)) + '/' + m.group(2)

def replace_makefiledir(m):
    w = makefiledir[int(m.group(1)) - 1]
    dir_name = os.path.dirname(path)
    
    if dir_name != '/':
        dir_name += '/'

    return '<a href="'+version+'/source'+dir_name+w+'/Makefile">'+w+'/</a>'

makefiledir_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '([-\w]+)/(\s+|$)',
                'prefunc': keep_makefiledir,
                'postrex': '__KEEPMAKEFILEDIR__(\d+)/',
                'postfunc': replace_makefiledir
                }

filters.append(makefiledir_filters)
