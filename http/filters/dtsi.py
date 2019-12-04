# Filters for dts includes as follows:
# /include/ "file"

dtsi = []

def keep_dtsi(match):
    dtsi.append(match.group(3))
    return match.group(1) + '/include/' + match.group(2) + '"__KEEPDTSI__' + str(len(dtsi)) + '"'

def replace_dtsi(match):
    w = dtsi[int(match.group(1)) - 1]
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
