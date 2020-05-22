# Elixir Python definitions for Linux

exec(open('dtsi.py').read())
exec(open('commonkconfig.py').read())
exec(open('makefileo.py').read())
exec(open('makefiledtb.py').read())
exec(open('makefiledir.py').read())
exec(open('makefilefile.py').read())
exec(open('makefilesubdir.py').read())
exec(open('makefilesrctree.py').read())

exec(open('cpppathinc.py').read())
# include/uapi contains includes to user headers under #ifndef __KERNEL__
# Our solution is to ignore all includes in such paths
cpppathinc_filters['path_exceptions'] = {'^/include/uapi/.*'}
