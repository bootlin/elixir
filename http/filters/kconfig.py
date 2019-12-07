# Filters for Kconfig includes

kconfig = []

def keep_kconfig(m):
    kconfig.append(m.group(4))
    return m.group(1) + m.group(2) + m.group(3) + '"__KEEPKCONFIG__' + str(len(kconfig)) + '"'

def replace_kconfig(m):
    w = kconfig[int(m.group(1)) - 1]
    return '<a href="'+version+'/source/'+w+'">'+w+'</a>'

kconfig_filters = {
                'case': 'filename',
                'match': {'Kconfig'},
                'prerex': '^(\s*)(source)(\s*)\"(.*?)\"',
                'prefunc': keep_kconfig,
                'postrex': '__KEEPKCONFIG__(\d+)',
                'postfunc': replace_kconfig
                }

filters.append(kconfig_filters)
