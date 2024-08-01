# Elixir Python definitions for qemu

from filters.kconfig import KconfigFilter
from filters.kconfigidents import KconfigIdentsFilter
from filters.defconfig import DefConfigIdentsFilter

new_filters.extend([
    KconfigFilter(),
    KconfigIdentsFilter(),
    DefConfigIdentsFilter(),
])

