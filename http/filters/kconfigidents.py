# Filter for kconfig identifier links

kconfigidents = []

def keep_kconfigidents(m):
    kconfigidents.append(m.group(1))
    return '__KEEPKCONFIGIDENTS__' + encode_number(len(kconfigidents))

def replace_kconfigidents(m):
    i = kconfigidents[decode_number(m.group(2)) - 1]

    n = i
    #Remove the CONFIG_ when we are in a Kconfig file
    if family == 'K':
        n = n[7:]

    return str(m.group(1) or '') + '<a href="'+version+'/K/ident/'+i+'">'+n+'</a>'

kconfigident_filters = {
                'case': 'any',
                'prerex': '\033\[31m(?=CONFIG_)(.*?)\033\[0m',
                'prefunc': keep_kconfigidents,
                'postrex': '__(<.+?>)?KEEPKCONFIGIDENTS__([A-J]+)',
                'postfunc': replace_kconfigidents
                }

filters.append(kconfigident_filters)
