from os.path import dirname
import re
from filters.utils import Filter, FilterContext, decode_number, encode_number, filename_without_ext_matches

# Filters for Makefile file includes like these:
# file.o
# Example: u-boot/v2023.10/source/Makefile#L1767
class MakefileOFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.makefileo = []

    def check_if_applies(self, ctx) -> bool:
        return super().check_if_applies(ctx) and \
                filename_without_ext_matches(ctx.path, {'Makefile'})

    def transform_raw_code(self, ctx, code: str) -> str:
        def keep_makefileo(m):
            self.makefileo.append(m.group(1))
            return f'__KEEPMAKEFILEO__{ encode_number(len(self.makefileo)) }.o'

        return re.sub('(?<=\s)([-\w/]+)\.o(?!\w)(?! :?=)', keep_makefileo, code, flags=re.MULTILINE)

    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        def replace_makefileo(m):
            w = self.makefileo[decode_number(m.group(1)) - 1]

            dir_name = dirname(ctx.path)
            if dir_name != '/':
                dir_name += '/'

            npath = f'{ dir_name }{ w }.c'
            return f'<a href="{ ctx.get_absolute_source_url(npath) }">{ w }.o</a>'

        return re.sub('__KEEPMAKEFILEO__([A-J]+)\.o', replace_makefileo, html, flags=re.MULTILINE)

