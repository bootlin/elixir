# Filters for Config.in includes

configin = []

def keep_configin(m):
    configin.append(m.group(4))
    return m.group(1) + m.group(2) + m.group(3) + '"__KEEPCONFIGIN__' + encode_number(len(configin)) + '"'

def replace_configin(m):
    w = configin[decode_number(m.group(1)) - 1]
    return '<a href="'+version+'/source/'+w+'">'+w+'</a>'

configin_filters = {
                'case': 'filename',
                'match': {'Config'},
                'prerex': '^(\s*)(source)(\s*)\"(.*)\"',
                'prefunc': keep_configin,
                'postrex': '__KEEPCONFIGIN__([A-J]+)',
                'postfunc': replace_configin
                }

filters.append(configin_filters)
