# Filters for cpp includes like these:
# #include <file>

# Such filters work typically for standalone projects (like kernels and bootloaders)
# If we make references to other projects, we could
# end up with links to headers which are outside the project

cpppathinc = []

def keep_cpppathinc(m):
    m1 = m.group(1)
    m2 = m.group(2)
    inc = m.group(3)
    if re.match('^asm/.*', inc):
        # Keep the original string in case the path contains "asm/"
        # Because there are then multiple include possibilites, one per architecture
        return m1 + '#include' + m2 + '<' + inc + '>'
    else:
        cpppathinc.append(inc)
        return m1 + '#include' + m2 + '<__KEEPCPPPATHINC__' + str(len(cpppathinc)) + '>'

def replace_cpppathinc(m):
    w = cpppathinc[int(m.group(1)) - 1]
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
