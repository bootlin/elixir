# Filter for identifier links

idents = []

def keep_idents(m):
    idents.append(m.group(1))
    return '__KEEPIDENTS__' + encode_number(len(idents))

def replace_idents(m):
    i = idents[decode_number(m.group(1)) - 1]
    return '<a href="'+version+'/ident/'+i+'">'+i+'</a>'

ident_filters = {
                'case': 'any',
                'prerex': '\033\[31m(.*?)\033\[0m',
                'prefunc': keep_idents,
                'postrex': '__KEEPIDENTS__([A-J]+)',
                'postfunc': replace_idents
                }

filters.append(ident_filters)
