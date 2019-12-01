#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2019 Michael Opdenacker
#  <michael.opdenacker@bootlin.com>
#
#  Elixir is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Elixir is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Elixir.  If not, see <http://www.gnu.org/licenses/>.

# Generic settings

filters = []

# Filter for identifier links

idents = []

def keep_idents(match):
    idents.append(match.group(1))
    return '__KEEPIDENTS__' + str(len(idents))

def replace_idents(match):
    i = idents[int(match.group(1)) - 1]
    return '<a href="'+version+'/ident/'+i+'">'+i+'</a>'

ident_filters = {
                'case': 'any',
                'prerex': '\033\[31m(.*?)\033\[0m',
                'prefunc': keep_idents,
                'postrex': '__KEEPIDENTS__(\d+)',
                'postfunc': replace_idents
                }

filters.append(ident_filters)

# Filters for dts includes

dtsi = []

def keep_dtsi(match):
    dtsi.append(match.group(4))
    return match.group(1) + match.group(2) + match.group(3) + '"__KEEPDTSI__' + str(len(dtsi)) + '"'

def replace_dtsi(match):
    w = dtsi[int(match.group(1)) - 1]
    return '<a href="'+version+'/source'+os.path.dirname(path)+'/'+w+'">'+w+'</a>'

dtsi_filters = {
                'case': 'extension',
                'match': {'dts', 'dtsi'},
                'prerex': '^(\s*)(#include|/include/)(\s*)\"(.*?)\"',
                'prefunc': keep_dtsi,
                'postrex': '__KEEPDTSI__(\d+)',
                'postfunc': replace_dtsi
                }

filters.append(dtsi_filters)

# Filters for Kconfig includes

kconfig = []

def keep_kconfig(match):
    kconfig.append(match.group(4))
    return match.group(1) + match.group(2) + match.group(3) + '"__KEEPKCONFIG__' + str(len(kconfig)) + '"'

def replace_kconfig(match):
    w = kconfig[int(match.group(1)) - 1]
    return '<a href="'+version+'/source/'+w+'">'+w+'</a>'

kconfig_filters = {
                'case': 'filename',
                'match': {'Kconfig'},
                'prerex': '^(\s*)(source)(\s*)\"(.*?)\"',
                'prefunc': keep_kconfig,
                'postrex': '__KEEPKCONFIG__(\d+)',
                'postfunc': replace_kconfig
                }

filters.append(kconfig_filters)
