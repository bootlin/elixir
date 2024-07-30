# Common filters
from filters.utils import encode_number, decode_number

new_filters = []
filters = []
exec(open('dtscomp.py').read())
exec(open('ident.py').read())
exec(open('cppinc.py').read())
