# Filters for Makefile file includes like these:
# obj-y += file.o

makefileo = []

def keep_makefileo(match):
    makefileo.append(match.group(1))
    return '__KEEPMAKEFILEO__' + str(len(makefileo)) + '.o'

def replace_makefileo(match):
    w = makefileo[int(match.group(1)) - 1]
    return '<a href="'+version+'/source'+os.path.dirname(path)+'/'+w+'.c">'+w+'.o</a>'

makefileo_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '(\w+)\.o',
                'prefunc': keep_makefileo,
                'postrex': '__KEEPMAKEFILEO__(\d+)\.o',
                'postfunc': replace_makefileo
                }

filters.append(makefileo_filters)
