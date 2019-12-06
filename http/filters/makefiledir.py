# Filters for Makefile directory includes as follows:
# obj-$(VALUE) += dir/

makefiledir = []

def keep_makefiledir(match):
    makefiledir.append(match.group(1))
    return '__KEEPMAKEFILEDIR__' + str(len(makefiledir)) + '/' + match.group(2)

def replace_makefiledir(match):
    w = makefiledir[int(match.group(1)) - 1]
    return '<a href="'+version+'/source'+os.path.dirname(path)+'/'+w+'/Makefile">'+w+'/</a>'

makefiledir_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '([-\w]+)/(\s*|$)',
                'prefunc': keep_makefiledir,
                'postrex': '__KEEPMAKEFILEDIR__(\d+)/',
                'postfunc': replace_makefiledir
                }

filters.append(makefiledir_filters)
