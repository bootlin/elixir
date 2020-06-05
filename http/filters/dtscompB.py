# Filter for DT compatible strings in documentation files

dtscompB = []

def keep_dtscompB(m):
    text = m.group(1)

    if query('dts-comp-exists', parse.quote(text)):
        dtscompB.append(text)
        return '__KEEPDTSCOMPB__' + encode_number(len(dtscompB))
    else:
        return m.group(0)

def replace_dtscompB(m):
    i = dtscompB[decode_number(m.group(1)) - 1]

    return '<a href="'+version+'/B/ident/'+parse.quote(i)+'">'+i+'</a>'

dtscompB_filters = {
                'case': 'path',
                'match': {'/Documentation/devicetree/bindings'},
                'prerex': '([\w-]+,?[\w-]+)',
                'prefunc': keep_dtscompB,
                'postrex': '__KEEPDTSCOMPB__([A-J]+)',
                'postfunc': replace_dtscompB
                }

filters.append(dtscompB_filters)
