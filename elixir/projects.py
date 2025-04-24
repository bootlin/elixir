from .filters import *

# Dictionary of custom per-projects settings.
# filters:
# Projects not present in this dictionary only use default_filters.
# Use `*` to unpack filter lists defined above,
# you can pass additional options to filters by putting a Filter
# class and a dictionary with options in a tuple, like this:
# (FilterCls, {"option": True}).
# Check filter files and utils.py for information about available options
projects = {
    'amazon-freertos': {
        'filters': [
            *default_filters,
            MakefileSubdirFilter,
        ],
    },
    'arm-trusted-firmware': {
        'filters': [
            *default_filters,
            CppPathIncFilter,
        ],
    },
    'barebox': {
        'filters': [
            *default_filters,
            DtsiFilter,
            *common_kconfig_filters,
            CppPathIncFilter,
            *common_makefile_filters,
        ],
    },
    'coreboot': {
        'filters': [
            *default_filters,
            DtsiFilter,
            *common_kconfig_filters,
            *common_makefile_filters,
        ],
    },
    'linux': {
        'filters': [
            *default_filters,
            DtsiFilter,
            *common_kconfig_filters,
            *common_makefile_filters,
            # include/uapi contains includes to user headers under #ifndef __KERNEL__
            # Our solution is to ignore all includes in such paths
            (CppPathIncFilter, {"path_exceptions": {'^/include/uapi/.*'}}),
        ],
    },
    'qemu': {
        'filters': [
            *default_filters,
            *common_kconfig_filters,
        ],
    },
    'u-boot': {
        'filters': [
            *default_filters,
            DtsiFilter,
            *common_kconfig_filters,
            CppPathIncFilter,
            *common_makefile_filters,
        ],
    },
    'uclibc-ng': {
        'filters': [
            *default_filters,
            ConfigInFilter,
        ],
    },
    'zephyr': {
        'filters': [
            *default_filters,
            DtsiFilter,
            *common_kconfig_filters,
            CppPathIncFilter,
        ],
    },
}

