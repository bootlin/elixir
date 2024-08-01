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

# Dictionary of custom per-projects filters.
# Projects not in present this dictionary only use default_filters.
# Use `*` to unpack filter lists defined above,
# you can pass additional options to filters by putting the Filter
# class and a dictionary with options in a tuple, like this:
# (FilterCls, {"option": True}).
# Check filter files and utils.py for information about available options
project_filters = {
    'amazon-freertos': [
        *default_filters,
        MakefileSubdirFilter,
    ],
    'arm-trusted-firmware': [
        *default_filters,
        CppPathIncFilter,
    ],
    'barebox': [
        *default_filters,
        DtsiFilter,
        *common_kconfig_filters,
        CppPathIncFilter,
        *common_makefile_filters,
    ],
    'coreboot': [
        *default_filters,
        DtsiFilter,
        *common_kconfig_filters,
        *common_makefile_filters,
    ],
    'linux': [
        *default_filters,
        DtsiFilter,
        *common_kconfig_filters,
        *common_makefile_filters,
        # include/uapi contains includes to user headers under #ifndef __KERNEL__
        # Our solution is to ignore all includes in such paths
        (CppPathIncFilter, {"path_exceptions": {'^/include/uapi/.*'}}),
    ],
    'qemu': [
        *default_filters,
        *common_kconfig_filters,
    ],
    'u-boot': [
        *default_filters,
        DtsiFilter,
        *common_kconfig_filters,
        CppPathIncFilter,
        *common_makefile_filters,
    ],
    'uclibc-ng': [
        *default_filters,
        ConfigInFilter,
    ],
    'zephyr': [
        *default_filters,
        DtsiFilter,
        *common_kconfig_filters,
        CppPathIncFilter,
    ],
}

