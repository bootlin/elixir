import re
from filters.utils import Filter, FilterContext, encode_number, decode_number, extension_matches

# Filter for DT compatible strings in DTS (D family) files
# compatible = "device"
# Example: u-boot/v2023.10/source/arch/arm/dts/ac5-98dx35xx-rd.dts#L37
class DtsCompDtsFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dtscompD = []

    def check_if_applies(self, ctx) -> bool:
        return super().check_if_applies(ctx) and \
            ctx.query.query('dts-comp') and \
            extension_matches(ctx.path, {'dts', 'dtsi'})

    def transform_raw_code(self, ctx, code: str) -> str:
        def sub_func(m):
            match = m.group(0)
            strings = re.findall("\"(.+?)\"", m.group(1))

            for string in strings:
                self.dtscompD.append(string)
                match = match.replace(string, '__KEEPDTSCOMPD__' + encode_number(len(self.dtscompD)))

            return match

        return re.sub('\s*compatible(.*?)$', sub_func, code, flags=re.MULTILINE)

    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        def replace_dtscompD(m):
            i = self.dtscompD[decode_number(m.group(1)) - 1]

            return f'<a class="ident" href="{ ctx.get_ident_url(i, "B") }">{ i }</a>'

        return re.sub('__KEEPDTSCOMPD__([A-J]+)', replace_dtscompD, html, flags=re.MULTILINE)

