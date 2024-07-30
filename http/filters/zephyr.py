# Elixir Python definitions for Zephyr

from filters.dtsi import DtsiFilter

new_filters.append(DtsiFilter())

exec(open('commonkconfig.py').read())
exec(open('cpppathinc.py').read())
