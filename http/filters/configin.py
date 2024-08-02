import re
from filters.utils import Filter, FilterContext, decode_number, encode_number, filename_without_ext_matches

# Filters for Config.in includes
# source "path/file"
# Example: uclibc-ng/v1.0.47/source/extra/Configs/Config.in#L176
class ConfigInFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configin = []

    def check_if_applies(self, ctx) -> bool:
        return super().check_if_applies(ctx) and \
                filename_without_ext_matches(ctx.filepath, {'Config'})

    def transform_raw_code(self, ctx, code: str) -> str:
        def keep_configin(m):
            self.configin.append(m.group(4))
            return f'{ m.group(1) }{ m.group(2) }{ m.group(3) }"__KEEPCONFIGIN__{ encode_number(len(self.configin)) }"'

        return re.sub('^(\s*)(source)(\s*)\"(.*)\"', keep_configin, code, flags=re.MULTILINE)

    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        def replace_configin(m):
            w = self.configin[decode_number(m.group(1)) - 1]
            return f'<a href="{ ctx.get_absolute_source_url(w) }">{ w }</a>'

        return re.sub('__KEEPCONFIGIN__([A-J]+)', replace_configin, html, flags=re.MULTILINE)

