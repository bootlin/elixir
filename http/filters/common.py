# Common filters
from filters.utils import encode_number, decode_number
from filters.ident import IdentFilter

new_filters = [
    IdentFilter(),
]
filters = []
exec(open('dtscomp.py').read())
exec(open('cppinc.py').read())
