# Elixir Python definitions for Coreboot

from filters.dtsi import DtsiFilter

from filters.kconfig import KconfigFilter
from filters.kconfigidents import KconfigIdentsFilter
from filters.defconfig import DefConfigIdentsFilter

new_filters.extend([
    DtsiFilter(),

    KconfigFilter(),
    KconfigIdentsFilter(),
    DefConfigIdentsFilter(),
])

