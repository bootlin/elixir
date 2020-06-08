# Filter for DT compatible strings in C files

dtscompC = []

def keep_dtscompC(m):
    dtscompC.append(m.group(4))
    return m.group(1) + '"__KEEPDTSCOMPC__' + encode_number(len(dtscompC)) + '"'

def replace_dtscompC(m):
    i = dtscompC[decode_number(m.group(1)) - 1]

    return '<a href="'+version+'/B/ident/'+parse.quote(i)+'">'+i+'</a>'

dtscompC_filters = {
                'case': 'extension',
                'match': {'c', 'cc', 'cpp', 'c++', 'cxx', 'h', 's'},
                'prerex': '(\s*{*\s*\.(\033\[31m)?compatible(\033\[0m)?\s*=\s*)\"(.+?)\"',
                'prefunc': keep_dtscompC,
                'postrex': '__KEEPDTSCOMPC__([A-J]+)',
                'postfunc': replace_dtscompC
                }

filters.append(dtscompC_filters)
