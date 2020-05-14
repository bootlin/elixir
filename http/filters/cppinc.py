# Filters for cpp includes like these:
# #include "file"

cppinc = []

def keep_cppinc(m):
    cppinc.append(m.group(3))
    return m.group(1) + '#include' + m.group(2) + '"__KEEPCPPINC__' + encode_number(len(cppinc)) + '"'

def replace_cppinc(m):
    w = cppinc[decode_number(m.group(1)) - 1]
    return '<a href="'+version+'/source'+os.path.dirname(path)+'/'+w+'">'+w+'</a>'

cppinc_filters = {
                'case': 'extension',
                'match': {'dts', 'dtsi', 'c', 'cc', 'cpp', 'c++', 'cxx', 'h', 's'},
                'prerex': '^(\s*)#include(\s*)\"(.*?)\"',
                'prefunc': keep_cppinc,
                'postrex': '__KEEPCPPINC__([A-J]+)',
                'postfunc': replace_cppinc
                }

filters.append(cppinc_filters)
