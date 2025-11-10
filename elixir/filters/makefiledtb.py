from os.path import dirname
import re
from .utils import Filter, FilterContext, decode_number, encode_number, filename_without_ext_matches, format_source_link

# Filters for Makefile file includes like these:
# dtb-y += file.dtb
# Example: u-boot/v2023.10/source/Makefile#L992
class MakefileDtbFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.makefiledtb = []

    def check_if_applies(self, ctx) -> bool:
        return super().check_if_applies(ctx) and \
                filename_without_ext_matches(ctx.filepath, {'Makefile'})

    def transform_raw_code(self, ctx, code: str) -> str:
        def keep_makefiledtb(m):
            self.makefiledtb.append(m.group(1))
            return f'__KEEPMAKEFILEDTB__{ encode_number(len(self.makefiledtb)) }.dtb'

        return re.sub('(?<=\s)([-\w/+\.]+)\.dtb', keep_makefiledtb, code, flags=re.MULTILINE)

    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        def replace_makefiledtb(m):
            w = self.makefiledtb[decode_number(m.group(1)) - 1]
            filedir = dirname(ctx.filepath)

            if filedir != '/':
                filedir += '/'

            npath = f'{ filedir }{ w }.dts'
            return format_source_link(ctx.get_absolute_source_url(npath), w+'.dtb')

        return re.sub('__KEEPMAKEFILEDTB__([A-J]+)\.dtb', replace_makefiledtb, html, flags=re.MULTILINE)

