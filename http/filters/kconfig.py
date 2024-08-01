import re
from filters.utils import Filter, FilterContext, encode_number, decode_number, filename_without_ext_matches

# Filters for Kconfig includes
# Replaces KConfig includes (source keyword) with links to included files
# `source "path/file"`
# Example: u-boot/v2023.10/source/Kconfig#L10
class KconfigFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kconfig = []

    def check_if_applies(self, ctx) -> bool:
        return super().check_if_applies(ctx) and \
                filename_without_ext_matches(ctx.filepath, {'Kconfig'})

    def transform_raw_code(self, ctx, code: str) -> str:
        def keep_kconfig(m):
            self.kconfig.append(m.group(4))
            return f'{ m.group(1) }{ m.group(2) }{ m.group(3) }"__KEEPKCONFIG__{ encode_number(len(self.kconfig)) }"'

        return re.sub('^(\s*)(source)(\s*)\"([\w/_\.-]+)\"', keep_kconfig, code, flags=re.MULTILINE)

    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        def replace_kconfig(m):
            w = self.kconfig[decode_number(m.group(1)) - 1]
            return f'<a href="{ ctx.get_absolute_source_url(w) }">{ w }</a>'

        return re.sub('__KEEPKCONFIG__([A-J]+)', replace_kconfig, html, flags=re.MULTILINE)

