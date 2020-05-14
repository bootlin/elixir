# Filters for Makefile directory includes as follows:
# subdir-y += dir

makefilesubdir = []

def keep_makefilesubdir(m):
    makefilesubdir.append(m.group(5))
    return m.group(1)+m.group(2)+m.group(3)+m.group(4)+'__KEEPMAKESUBDIR__' + encode_number(len(makefilesubdir)) + m.group(6)

def replace_makefilesubdir(m):
    w = makefilesubdir[decode_number(m.group(1)) - 1]

    dir_name = os.path.dirname(path)
    
    if dir_name != '/':
        dir_name += '/'

    return '<a href="'+version+'/source'+dir_name+w+'/Makefile">'+w+'</a>'

makefilesubdir_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '(subdir-y)(\s+)(\+=|:=)(\s+)([-\w]+)(\s*|$)',
                'prefunc': keep_makefilesubdir,
                'postrex': '__KEEPMAKESUBDIR__([A-J]+)',
                'postfunc': replace_makefilesubdir
                }

filters.append(makefilesubdir_filters)
