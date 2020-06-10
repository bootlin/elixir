#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2017--2020  Maxime Chretien <maxime.chretien@bootlin.com>
#                            and contributors
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

import re
from urllib import parse
from lib import decode

class FindCompatibleDTS:
    def __init__(self):
        # Compile regexes
        self.regex_c = re.compile("\s*{*\s*\.compatible\s*=\s*\"(.+?)\"")
        self.regex_dts1 = re.compile("\s*compatible")
        self.regex_dts2 = re.compile("\"(.+?)\"")
        self.regex_bindings = re.compile("([\w-]+,?[\w-]+)")

    def parse_c(self, content):
        return self.regex_c.findall(content)

    def parse_dts(self, content):
        ret = []
        if self.regex_dts1.match(content) != None:
            ret = self.regex_dts2.findall(content)
        return ret

    def parse_bindings(self, content):
        # There are a lot of wrong results
        # but we don't apply that to a lot of files
        # so it should be fine
        return self.regex_bindings.findall(content)

    def run(self, file_lines, family):
        ident_list = []

        # Iterate though lines and search for idents
        for num, line in enumerate(file_lines, 1):
            line = decode(line)
            if family == 'C':
                ret = self.parse_c(line)
            elif family == 'D':
                ret = self.parse_dts(line)
            elif family == 'B':
                ret = self.parse_bindings(line)

            for i in range(len(ret)):
                ident_list.append(str(parse.quote(ret[i])) + ' ' + str(num))

        return ident_list

