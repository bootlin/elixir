# Elixir Python definitions for Barebox

from filters.dtsi import DtsiFilter

from filters.cpppathinc import CppPathIncFilter

exec(open('commonkconfig.py').read())
exec(open('makefileo.py').read())
exec(open('makefiledtb.py').read())
exec(open('makefiledir.py').read())
exec(open('makefilefile.py').read())
exec(open('makefilesubdir.py').read())
exec(open('makefilesrctree.py').read())

new_filters.extend([
    DtsiFilter(),

    CppPathIncFilter(),
])
