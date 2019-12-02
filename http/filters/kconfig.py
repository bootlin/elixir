# Filters for Kconfig includes

kconfig = []

def keep_kconfig(match):
    kconfig.append(match.group(4))
    return match.group(1) + match.group(2) + match.group(3) + '"__KEEPKCONFIG__' + str(len(kconfig)) + '"'

def replace_kconfig(match):
    w = kconfig[int(match.group(1)) - 1]
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
