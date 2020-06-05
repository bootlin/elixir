# Filter for DT compatible strings in D files

dtscompD = []

def keep_dtscompD(m):
    match = m.group(0)
    strings = re.findall("\"(.+?)\"", m.group(1))

    for string in strings:
        dtscompD.append(string)
        match = match.replace(string, '__KEEPDTSCOMPD__' + encode_number(len(dtscompD)))

    return match

def replace_dtscompD(m):
    i = dtscompD[decode_number(m.group(1)) - 1]

    return '<a href="'+version+'/B/ident/'+parse.quote(i)+'">'+i+'</a>'

dtscompD_filters = {
                'case': 'extension',
                'match': {'dts', 'dtsi'},
                'prerex': '\s*compatible(.*?)$',
                'prefunc': keep_dtscompD,
                'postrex': '__KEEPDTSCOMPD__([A-J]+)',
                'postfunc': replace_dtscompD
                }

filters.append(dtscompD_filters)
