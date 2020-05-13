# Filters for Makefile file includes like these:
# file.o

makefileo = []

def keep_makefileo(m):
    makefileo.append(m.group(1))
    return '__KEEPMAKEFILEO__' + str(len(makefileo)) + '.o'

def replace_makefileo(m):
    w = makefileo[int(m.group(1)) - 1]

    dir_name = os.path.dirname(path)
    
    if dir_name != '/':
        dir_name += '/'

    return '<a href="'+version+'/source'+dir_name+w+'.c">'+w+'.o</a>'

makefileo_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '([-\w]+)\.o(?!\w)',
                'prefunc': keep_makefileo,
                'postrex': '__KEEPMAKEFILEO__(\d+)\.o',
                'postfunc': replace_makefileo
                }

filters.append(makefileo_filters)
