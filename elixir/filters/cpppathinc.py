import re
from .utils import Filter, FilterContext, encode_number, decode_number, extension_matches, format_source_link

# Filters for cpp includes like these:
# #include <file>

# Such filters work typically for standalone projects (like kernels and bootloaders)
# If we make references to other projects, we could
# end up with links to headers which are outside the project
# Example: u-boot/v2023.10/source/env/embedded.c#L16
class CppPathIncFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cpppathinc = []

    def check_if_applies(self, ctx) -> bool:
        return super().check_if_applies(ctx) and \
                extension_matches(ctx.filepath, {'dts', 'dtsi', 'c', 'cc', 'cpp', 'c++', 'cxx', 'h', 's'})

    def transform_raw_code(self, ctx, code: str) -> str:
        def keep_cpppathinc(m):
            m1 = m.group(1)
            m2 = m.group(2)
            inc = m.group(3)
            if re.match('^asm/.*', inc):
                # Keep the original string in case the path contains "asm/"
                # Because there are then multiple include possibilites, one per architecture
                return m.group(0)
            else:
                self.cpppathinc.append(inc)
                return f'{ m1 }#include{ m2 }<__KEEPCPPPATHINC__{ encode_number(len(self.cpppathinc)) }>'

        return re.sub('^(\s*)#include(\s*)<(.*?)>', keep_cpppathinc, code, flags=re.MULTILINE)

    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        def replace_cpppathinc(m):
            w = self.cpppathinc[decode_number(m.group(1)) - 1]
            path = f'/include/{ w }'
            return format_source_link(ctx.get_absolute_source_url(path), w)

        return re.sub('__KEEPCPPPATHINC__([A-J]+)', replace_cpppathinc, html, flags=re.MULTILINE)

