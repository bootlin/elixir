# Elixir Python definitions for U-Boot

from filters.dtsi import DtsiFilter

new_filters.append(DtsiFilter())

exec(open('commonkconfig.py').read())
exec(open('cpppathinc.py').read())
exec(open('makefileo.py').read())
exec(open('makefiledtb.py').read())
exec(open('makefiledir.py').read())
exec(open('makefilesubdir.py').read())
exec(open('makefilefile.py').read())
exec(open('makefilesrctree.py').read())
