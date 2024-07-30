import re
from filters.utils import Filter, FilterContext, encode_number, decode_number

# Filter for identifier links
# Replaces identifiers marked by Query.query('file') with links to ident page.
# If Query.query('file') detects that a file belongs to a family that can contain
# indexed identifiers, it processes the file by adding unprintable markers
# ('\033[31m' + token + b'\033[0m') to tokens that have an entry in the definitions
# database. This filter replaces these marked tokens with links to their ident pages,
# unless the token starts with CONFIG_ - these tokens are handled by the Kconfig filter.
class IdentFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.idents = []

    def transform_raw_code(self, ctx, code: str) -> str:
        def sub_func(m):
            self.idents.append(m.group(1))
            return '__KEEPIDENTS__' + encode_number(len(self.idents))

        return re.sub('\033\[31m(?!CONFIG_)(.*?)\033\[0m', sub_func, code, flags=re.MULTILINE)

    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        def sub_func(m):
            i = self.idents[decode_number(m.group(2)) - 1]
            link = f'<a class="ident" href="{ ctx.get_ident_url(i) }">{ i }</a>'
            return str(m.group(1) or '') + link

        return re.sub('__(<.+?>)?KEEPIDENTS__([A-J]+)', sub_func, html, flags=re.MULTILINE)

