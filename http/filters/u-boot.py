# Elixir Python definitions for U-Boot

from filters.dtsi import DtsiFilter
from filters.cpppathinc import CppPathIncFilter

from filters.kconfig import KconfigFilter
from filters.kconfigidents import KconfigIdentsFilter
from filters.defconfig import DefConfigIdentsFilter

from filters.makefileo import MakefileOFilter
from filters.makefiledtb import MakefileDtbFilter
from filters.makefiledir import MakefileDirFilter
from filters.makefilesubdir import MakefileSubdirFilter
from filters.makefilefile import MakefileFileFilter
from filters.makefilesrctree import MakefileSrcTreeFilter

new_filters.extend([
    DtsiFilter(),

    CppPathIncFilter(),

    KconfigFilter(),
    KconfigIdentsFilter(),
    DefConfigIdentsFilter(),

    MakefileOFilter(),
    MakefileDtbFilter(),
    MakefileDirFilter(),
    MakefileSubdirFilter(),
    MakefileFileFilter(),
    MakefileSrcTreeFilter(),
])

