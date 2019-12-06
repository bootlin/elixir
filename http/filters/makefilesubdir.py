# Filters for Makefile directory includes as follows:
# subdir-y += dir

makefilesubdir = []

def keep_makefilesubdir(m):
    makefilesubdir.append(m.group(5))
    return m.group(1)+m.group(2)+m.group(3)+m.group(4)+'__KEEPMAKESUBDIR__' + str(len(makefilesubdir)) + m.group(6)

def replace_makefilesubdir(m):
    w = makefilesubdir[int(m.group(1)) - 1]
    return '<a href="'+version+'/source'+os.path.dirname(path)+'/'+w+'/Makefile">'+w+'</a>'

makefilesubdir_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '(subdir-y)(\s+)(\+=|:=)(\s+)([-\w]+)(\s*|$)',
                'prefunc': keep_makefilesubdir,
                'postrex': '__KEEPMAKESUBDIR__(\d+)',
                'postfunc': replace_makefilesubdir
                }

filters.append(makefilesubdir_filters)
