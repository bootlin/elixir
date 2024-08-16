import re
from .utils import Filter, FilterContext, encode_number, decode_number, extension_matches

# Filter for DT compatible strings in code (C family) files
# Finds assigments to properties and variables named 'compatible' and recognized by the Query.query('file')
# .compatible = "device"
# Example: u-boot/v2023.10/source/drivers/phy/nop-phy.c#L84
class DtsCompCodeFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dtscompC = []

    def check_if_applies(self, ctx) -> bool:
        return super().check_if_applies(ctx) and \
            ctx.query.query('dts-comp') and \
            extension_matches(ctx.filepath, {'c', 'cc', 'cpp', 'c++', 'cxx', 'h', 's'})

    def transform_raw_code(self, ctx, code: str) -> str:
        # quit early if source file does not contain any strings that could be an assignment to a 'compatible' property
        # this is much faster than the match-and-replace regex, especially for big files
        compatible_search = re.search('\.(\033\[31m)?compatible(\033\[0m)?\s*=', code, flags=re.MULTILINE)
        if compatible_search is None:
            return code

        def keep_dtscompC(m):
            self.dtscompC.append(m.group(4))
            return f'{ m.group(1) }"__KEEPDTSCOMPC__{ encode_number(len(self.dtscompC)) }"'

        return re.sub('(\s*{*\s*\.(\033\[31m)?compatible(\033\[0m)?\s*=\s*)\"(.+?)\"',
                      keep_dtscompC, code, flags=re.MULTILINE)

    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        def replace_dtscompC(m):
            i = self.dtscompC[decode_number(m.group(1)) - 1]
            return f'<a class="ident" href="{ ctx.get_ident_url(i, "B") }">{ i }</a>'

        return re.sub('__KEEPDTSCOMPC__([A-J]+)', replace_dtscompC, html, flags=re.MULTILINE)

