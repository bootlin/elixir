# Filters for Makefile file includes like these:
# dtb-y += file.dtb

makefiledtb = []

def keep_makefiledtb(m):
    makefiledtb.append(m.group(1))
    return '__KEEPMAKEFILEDTB__' + encode_number(len(makefiledtb)) + '.dtb'

def replace_makefiledtb(m):
    w = makefiledtb[decode_number(m.group(1)) - 1]

    dir_name = os.path.dirname(path)
    
    if dir_name != '/':
        dir_name += '/'

    return '<a href="'+version+'/source'+dir_name+w+'.dts">'+w+'.dtb</a>'

makefiledtb_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '(?<=\s)([-\w/+\.]+)\.dtb',
                'prefunc': keep_makefiledtb,
                'postrex': '__KEEPMAKEFILEDTB__([A-J]+)\.dtb',
                'postfunc': replace_makefiledtb
                }

filters.append(makefiledtb_filters)
