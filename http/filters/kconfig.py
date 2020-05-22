# Filters for Kconfig includes

kconfig = []

def keep_kconfig(m):
    kconfig.append(m.group(4))
    return m.group(1) + m.group(2) + m.group(3) + '"__KEEPKCONFIG__' + encode_number(len(kconfig)) + '"'

def replace_kconfig(m):
    w = kconfig[decode_number(m.group(1)) - 1]
    return '<a href="'+version+'/source/'+w+'">'+w+'</a>'

kconfig_filters = {
                'case': 'filename',
                'match': {'Kconfig'},
                'prerex': '^(\s*)(source)(\s*)\"([\w/_\.-]+)\"',
                'prefunc': keep_kconfig,
                'postrex': '__KEEPKCONFIG__([A-J]+)',
                'postfunc': replace_kconfig
                }

filters.append(kconfig_filters)
