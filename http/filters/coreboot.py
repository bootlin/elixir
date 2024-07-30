# Elixir Python definitions for Coreboot

from filters.dtsi import DtsiFilter

new_filters.append(DtsiFilter())
exec(open('commonkconfig.py').read())
