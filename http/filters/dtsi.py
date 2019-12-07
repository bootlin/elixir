# Filters for dts includes as follows:
# /include/ "file"

dtsi = []

def keep_dtsi(m):
    dtsi.append(m.group(3))
    return m.group(1) + '/include/' + m.group(2) + '"__KEEPDTSI__' + str(len(dtsi)) + '"'

def replace_dtsi(m):
    w = dtsi[int(m.group(1)) - 1]
    return '<a href="'+version+'/source'+os.path.dirname(path)+'/'+w+'">'+w+'</a>'

dtsi_filters = {
                'case': 'extension',
                'match': {'dts', 'dtsi'},
                'prerex': '^(\s*)/include/(\s*)\"(.*?)\"',
                'prefunc': keep_dtsi,
                'postrex': '__KEEPDTSI__(\d+)',
                'postfunc': replace_dtsi
                }

filters.append(dtsi_filters)
