from os.path import dirname
import re
from .utils import Filter, FilterContext, decode_number, encode_number, filename_without_ext_matches

# Filters for files listed in Makefiles
# path/file
# Example: u-boot/v2023.10/source/Makefile#L1509
class MakefileFileFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.makefilefile = []

    def check_if_applies(self, ctx) -> bool:
        return super().check_if_applies(ctx) and \
                filename_without_ext_matches(ctx.filepath, {'Makefile'})

    def transform_raw_code(self, ctx, code: str) -> str:
        def keep_makefilefile(m):
            filedir = dirname(ctx.filepath)

            if filedir != '/':
                filedir += '/'

            if ctx.query.file_exists(ctx.tag, filedir + m.group(1)):
                self.makefilefile.append(m.group(1))
                return f'__KEEPMAKEFILEFILE__{ encode_number(len(self.makefilefile)) }{ m.group(2) }'
            else:
                return m.group(0)

        return re.sub('(?:(?<=\s|=)|(?<=-I))(?!/)([-\w/]+/[-\w\.]+)(\s+|\)|$)', keep_makefilefile, code, flags=re.MULTILINE)

    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        def replace_makefilefile(m):
            w = self.makefilefile[decode_number(m.group(1)) - 1]
            filedir = dirname(ctx.filepath)

            if filedir != '/':
                filedir += '/'

            npath = filedir + w
            return f'<a href="{ ctx.get_absolute_source_url(npath) }">{ w }</a>'

        return re.sub('__KEEPMAKEFILEFILE__([A-J]+)', replace_makefilefile, html, flags=re.MULTILINE)

