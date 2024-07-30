# Common filters
from filters.utils import encode_number, decode_number
from filters.ident import IdentFilter
from filters.dtscompdocs import DtsCompDocsFilter
from filters.dtscompcode import DtsCompCodeFilter
from filters.dtscompdts import DtsCompDtsFilter

new_filters = [
    IdentFilter(),
]

if dts_comp_support:
    new_filters = [
        DtsCompDocsFilter(),
        DtsCompCodeFilter(),
        DtsCompDtsFilter(),
    ] + new_filters

filters = []
exec(open('cppinc.py').read())
