import re
from .utils import Filter, FilterContext, encode_number, decode_number, extension_matches

# Filter for kconfig identifier in defconfigs
# Replaces defconfig identifiers with links to definitions/references
# `CONFIG_OPTION=y`
# Example: u-boot/v2023.10/source/configs/A13-OLinuXino_defconfig#L1
class DefConfigIdentsFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defconfigidents = []

    def check_if_applies(self, ctx) -> bool:
        return super().check_if_applies(ctx) and \
                ctx.filepath.endswith('defconfig')

    def transform_raw_code(self, ctx, code: str) -> str:
        def keep_defconfigidents(m):
            self.defconfigidents.append(m.group(1))
            return '__KEEPDEFCONFIGIDENTS__' + encode_number(len(self.defconfigidents))

        return re.sub('(CONFIG_[\w]+)', keep_defconfigidents, code, flags=re.MULTILINE)

    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        def replace_defconfigidents(m):
            i = self.defconfigidents[decode_number(m.group(1)) - 1]
            return f'<a class="ident" href="{ ctx.get_ident_url(i, "K") }">{ i }</a>'

        return re.sub('__KEEPDEFCONFIGIDENTS__([A-J]+)', replace_defconfigidents, html, flags=re.MULTILINE)

