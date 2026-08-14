from .ident import IdentFilter

from .cppinc import CppIncFilter
from .cpppathinc import CppPathIncFilter

from .defconfig import DefConfigIdentsFilter
from .configin import ConfigInFilter

from .kconfig import KconfigFilter
from .kconfigidents import KconfigIdentsFilter

from .dtsi import DtsiFilter
from .dtscompdocs import DtsCompDocsFilter
from .dtscompcode import DtsCompCodeFilter
from .dtscompdts import DtsCompDtsFilter

from .makefileo import MakefileOFilter
from .makefiledtb import MakefileDtbFilter
from .makefiledir import MakefileDirFilter
from .makefilesubdir import MakefileSubdirFilter
from .makefilefile import MakefileFileFilter
from .makefilesrctree import MakefileSrcTreeFilter
from .makefilesubdir import MakefileSubdirFilter


# List of filters applied to all projects
default_filters = [
    DtsCompCodeFilter,
    DtsCompDtsFilter,
    DtsCompDocsFilter,
    IdentFilter,
    CppIncFilter,
]

# List of filters for Kconfig files
common_kconfig_filters = [
    KconfigFilter,
    KconfigIdentsFilter,
    DefConfigIdentsFilter,
]

# List of filters for Makefiles
common_makefile_filters = [
    MakefileOFilter,
    MakefileDtbFilter,
    MakefileDirFilter,
    MakefileFileFilter,
    MakefileSubdirFilter,
    MakefileSrcTreeFilter,
]

