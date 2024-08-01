# Elixir Python definitions for Zephyr

from filters.dtsi import DtsiFilter

from filters.cpppathinc import CppPathIncFilter

exec(open('commonkconfig.py').read())

new_filters.extend([
    DtsiFilter(),

    CppPathIncFilter(),
])

