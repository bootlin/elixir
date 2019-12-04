# Filters for cpp includes like these:
# #include "file"

cppinc = []

def keep_cppinc(match):
    cppinc.append(match.group(3))
    return match.group(1) + '#include' + match.group(2) + '"__KEEPCPPINC__' + str(len(cppinc)) + '"'

def replace_cppinc(match):
    w = cppinc[int(match.group(1)) - 1]
    return '<a href="'+version+'/source'+os.path.dirname(path)+'/'+w+'">'+w+'</a>'

cppinc_filters = {
                'case': 'extension',
                'match': {'dts', 'dtsi', 'c', 'cc', 'cpp', 'c++', 'cxx', 'h', 's'},
                'prerex': '^(\s*)#include(\s*)\"(.*?)\"',
                'prefunc': keep_cppinc,
                'postrex': '__KEEPCPPINC__(\d+)',
                'postfunc': replace_cppinc
                }

filters.append(cppinc_filters)
