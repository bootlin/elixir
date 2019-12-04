# Filters for cpp includes like these:
# #include <file>

# Such filters work typically for standalone projects (like kernels and bootloaders)
# If we make references to other projects, we could
# end up with links to headers which are outside the project

cpppathinc = []

def keep_cpppathinc(match):
    cpppathinc.append(match.group(3))
    return match.group(1) + '#include' + match.group(2) + '<__KEEPCPPPATHINC__' + str(len(cpppathinc)) + '>'

def replace_cpppathinc(match):
    w = cpppathinc[int(match.group(1)) - 1]
    return '<a href="'+version+'/source'+'/include/'+w+'">'+w+'</a>'

cpppathinc_filters = {
                'case': 'extension',
                'match': {'dts', 'dtsi', 'c', 'cc', 'cpp', 'c++', 'cxx', 'h', 's'},
                'prerex': '^(\s*)#include(\s*)<(.*?)>',
                'prefunc': keep_cpppathinc,
                'postrex': '__KEEPCPPPATHINC__(\d+)',
                'postfunc': replace_cpppathinc
                }

filters.append(cpppathinc_filters)
