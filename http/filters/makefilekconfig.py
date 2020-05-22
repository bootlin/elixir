# Filters for Kconfig used in Makefiles

makefilekconfig = []

def keep_makefilekconfig(m):
    makefilekconfig.append(m.group(1))
    return '$(__KEEPMAKEFILEKCONFIG__' + encode_number(len(makefilekconfig)) + ')'

def replace_makefilekconfig(m):
    i = makefilekconfig[decode_number(m.group(1)) - 1]
    return '<a href="'+version+'/K/ident/'+i+'">'+i+'</a>'

makefilekconfig_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '\$\((CONFIG_\w+)\)',
                'prefunc': keep_makefilekconfig,
                'postrex': '__KEEPMAKEFILEKCONFIG__([A-J]+)',
                'postfunc': replace_makefilekconfig
                }

filters.append(makefilekconfig_filters)
