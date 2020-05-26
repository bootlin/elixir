#!/usr/bin/env perl
# t/50-testhelpers.t: test TestHelpers.pm
#
# Copyright (c) 2020 Christopher White, <cxwembedded@gmail.com>.
# Copyright (c) 2020 D3 Engineering, LLC.
#
# Elixir is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Elixir is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# # You should have received a copy of the GNU Affero General Public License
# along with Elixir.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file uses core Perl modules only.

use FindBin '$Bin';
use lib $Bin;

use Test::More;

use TestEnvironment;
use TestHelpers qw(:all);

# === line_mark_string =======================================================

our ($fn, $refln, $ln);

sub level1 {
    eval line_mark_string 1, '$fn = __FILE__; $ln = __LINE__';
    ok !$@, 'level1 no errors';
}

$refln = __LINE__; level1;
is $fn, __FILE__, 'level1 file';
cmp_ok $ln, '==', $refln, 'level1 line';

sub level2 {
    level2_inner();
}

sub level2_inner {
    eval line_mark_string 2, '$fn = __FILE__; $ln = __LINE__';
    ok !$@, 'level2_inner no errors';
}

$refln = __LINE__; level2;
is $fn, __FILE__, 'level2 file';
cmp_ok $ln, '==', $refln, 'level2 line';

done_testing;
