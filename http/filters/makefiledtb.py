# Filters for Makefile file includes like these:
# dtb-y += file.dtb

makefiledtb = []

def keep_makefiledtb(m):
    makefiledtb.append(m.group(1))
    return '__KEEPMAKEFILEDTB__' + str(len(makefiledtb)) + '.dtb'

def replace_makefiledtb(m):
    w = makefiledtb[int(m.group(1)) - 1]
    return '<a href="'+version+'/source'+os.path.dirname(path)+'/'+w+'.dts">'+w+'.dtb</a>'

makefiledtb_filters = {
                'case': 'filename',
                'match': {'Makefile'},
                'prerex': '([-\w]+)\.dtb',
                'prefunc': keep_makefiledtb,
                'postrex': '__KEEPMAKEFILEDTB__(\d+)\.dtb',
                'postfunc': replace_makefiledtb
                }

filters.append(makefiledtb_filters)
