#!/usr/bin/env perl
# t/400-web.pl: Test web.py
#
# Copyright (c) 2020 Christopher White, <cxwembedded@gmail.com>.
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

# ===========================================================================
# Main

# Set up for the tests
my $tenv = TestEnvironment->new;
$tenv->build_repo(sibling_abs_path('tree'));	# dies on error
$tenv->build_db;
$tenv->update_env;

diag $tenv->report;

http_request_ok 'index query', $tenv, '/testproj/v5.4/source',
    [ qr{^Content-Type:\s*text/html}, qr{href="/testproj/v5.4/source/issue102.c"},
        qr{href="/testproj/v5.4/source/arch"},
        qr{href="/testproj/v5.4/source/python"},
        qr{<option value="P"}, qr{Python} ], 1;

http_request_ok 'identifier query', $tenv, '/testproj/v5.4/ident/gsb_buffer',
    [ qr{^Content-Type:\s*text/html}, qr{\bgsb_buffer\b},
        qr{source/drivers/i2c/i2c-core-acpi\.c#L23},
        qr{as a struct} ], 1;

# Doc comments: testcases pulled from t/300
http_request_ok 'doc-comment query (nonexistent)', $tenv,
    '/testproj/v5.4/ident/SOME_NONEXISTENT_IDENTIFIER_XYZZY_PLUGH',
    [ qr{^Content-Type:\s*text/html}, qr{Unknown identifier} ], 1;

http_request_ok 'doc-comment query (existent but not documented)', $tenv,
    '/testproj/v5.4/ident/gsb_buffer',   # in drivers/i2c/i2c-core-acpi.c
    [
        qr{^Content-Type:\s*text/html},
        { not => qr{\bDocumented in\b} },
    ], 1;

http_request_ok 'ident query (existent, function, documented in C file)', $tenv,
    '/testproj/v5.4/ident/i2c_acpi_get_i2c_resource',
    [
        qr{^Content-Type:\s*text/html},
        qr{\bDocumented in \d},
        qr{source/drivers/i2c/i2c-core-acpi\.c#L45},
    ], 1;

http_request_ok 'ident query (existent, function, documented in C file, #102)',
    $tenv, '/testproj/v5.4/ident/documented_function_XYZZY',
    [
        qr{^Content-Type:\s*text/html},
        qr{\bDocumented in \d},
        qr{source/issue102\.c#L6},
    ], 1;

http_request_ok 'python ident query', $tenv, '/testproj/v5.4/P/ident/py_make_widget',
    [
        qr{^Content-Type:\s*text/html},
        qr{python/py_widgets\.py},
        qr{line 16},
        qr{as a function},
        qr{python/py_consumer\.py},
        qr{<option value="P"},
        qr{\bPython\b},
    ], 1;

http_request_ok 'python ident is absent from the C family', $tenv,
    '/testproj/v5.4/C/ident/py_make_widget',
    [
        qr{^Content-Type:\s*text/html},
        qr{Unknown identifier 'py_make_widget'},
    ], 1;

http_request_ok 'python source links identifiers', $tenv,
    '/testproj/v5.4/source/python/py_widgets.py',
    [
        qr{^Content-Type:\s*text/html},
        qr{class="ident" href="/testproj/v5.4/P/ident/py_make_widget"},
        qr{class="ident" href="/testproj/v5.4/P/ident/PyWidget"},
        qr{py_make_widget in a comment should not count},
    ], 1;

done_testing;
