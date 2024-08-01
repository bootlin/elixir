# Elixir Python definitions for Zephyr

from filters.dtsi import DtsiFilter

from filters.cpppathinc import CppPathIncFilter

from filters.kconfig import KconfigFilter
from filters.kconfigidents import KconfigIdentsFilter
from filters.defconfig import DefConfigIdentsFilter

new_filters.extend([
    DtsiFilter(),

    CppPathIncFilter(),

    KconfigFilter(),
    KconfigIdentsFilter(),
    DefConfigIdentsFilter(),
])

