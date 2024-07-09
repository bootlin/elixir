#!/usr/bin/env perl
# 200-api.t: Test elixir's REST api against the files in tree/ .
#
# Copyright (c) 2020 Tamir Carmeli, <carmeli.tamir@gmail.com>.
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
use TestHelpers;

my $tenv = TestEnvironment->new;
$tenv->build_repo(sibling_abs_path('tree'))->build_db->update_env;

# Test the api using pytest. Prints the test results
run_produces_ok('api pytest suite', ["pytest", "-v", "t"], [], MUST_SUCCEED, 1);

done_testing;
