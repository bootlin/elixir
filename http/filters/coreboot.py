# Elixir Python definitions for Coreboot

from filters.dtsi import DtsiFilter

exec(open('commonkconfig.py').read())

new_filters.extend([
    DtsiFilter(),
])

