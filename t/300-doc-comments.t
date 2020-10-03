#!/usr/bin/env perl
# 300-doc-comments.t: Test elixir doc-comment extraction against the files in tree/ .
#
# Copyright (c) 2020 Christopher White.
# Copyright (c) 2020 D3 Engineering, LLC.
# By Christopher White, <cwhite@d3engineering.com>.
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
#
# You should have received a copy of the GNU Affero General Public License
# along with Elixir.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file uses core Perl modules only.

use autodie;    # note: still need to check system() calls manually

use FindBin '$Bin';
use lib $Bin;

use Test::More;

use TestEnvironment;
use TestHelpers;

# ===========================================================================
# Main

# Set up
my $tenv = TestEnvironment->new;
$tenv->build_repo(sibling_abs_path('tree'))->build_db->update_env;

ok_or_die( -d $tenv->lxr_data_dir, 'database dir exists',
    "Database dir @{[$tenv->lxr_data_dir]} not present");

# Spot-check some identifiers

run_produces_ok('doc-comment query (nonexistent)',
    [$tenv->query_py, qw(v5.4 ident SOME_NONEXISTENT_IDENTIFIER_XYZZY_PLUGH C)],
    [
        qr{^Documented in:},
        {doc => { not => qr{/} }},   # No file paths in the doc section
    ],
    MUST_SUCCEED);

run_produces_ok('doc-comment query (existent but not documented)',
    [$tenv->query_py, qw(v5.4 ident gsb_buffer C)],   # in drivers/i2c/i2c-core-acpi.c
    [
        qr{^Documented in:},
        {doc => { not => qr{/} }}
    ],
    MUST_SUCCEED);

run_produces_ok('ident query (existent, function, documented in C file)',
    [$tenv->query_py, qw(v5.4 ident i2c_acpi_get_i2c_resource C)],
    [
        qr{^Documented in:},
        {doc => qr{drivers/i2c/i2c-core-acpi\.c.+\b45\b}},
    ],
    MUST_SUCCEED);

run_produces_ok('ident query (existent, function, documented in C file, #102)',
    [$tenv->query_py, qw(v5.4 ident documented_function_XYZZY C)],
    [
        qr{^Documented in:},
        {doc => qr{issue102\.c.+\b6\b}},
    ],
    MUST_SUCCEED);

# Non-functions

run_produces_ok('ident query (existent, enum, documented in H file)',
    [$tenv->query_py, qw(v5.4 ident memblock_flags C)],
    [
        qr{^Documented in:},
        {doc => qr{\bmemblock\.h.+\b28\b}},
    ],
    MUST_SUCCEED);

run_produces_ok('ident query (existent, enum, not documented)',
    [$tenv->query_py, qw(v5.4 ident rseq_cpu_id_state C)],  # uapi/linux/rseq.h:16
    [
        qr{^Documented in:},
        {doc => { not => qr{/} }}
    ],
    MUST_SUCCEED);

run_produces_ok('ident query (existent, struct, documented in H file)',
    [$tenv->query_py, qw(v5.4 ident memblock_region C)],
    [
        qr{^Documented in:},
        {doc => qr{\bmemblock\.h.+\b42\b}},
    ],
    MUST_SUCCEED);

run_produces_ok('ident query (existent, struct, not documented)',
    [$tenv->query_py, qw(v5.4 ident epoll_event C)],    # eventpoll.h:77
    [
        qr{^Documented in:},
        {doc => { not => qr{/} }}
    ],
    MUST_SUCCEED);

run_produces_ok('ident query (existent, macro, documented in H file)',
    [$tenv->query_py, qw(v5.4 ident for_each_mem_range C)],
    [
        qr{^Documented in:},
        {doc => qr{\bmemblock\.h.+\b148\b}},
    ],
    MUST_SUCCEED);

run_produces_ok('ident query (existent, macro, not documented)',
    [$tenv->query_py, qw(v5.4 ident MEMBLOCK_LOW_LIMIT C)], # memblock.h:343
    [
        qr{^Documented in:},
        {doc => { not => qr{/} }}
    ],
    MUST_SUCCEED);

run_produces_ok('ident query (existent, macro, not documented)',
    [$tenv->query_py, qw(v5.4 ident MEMBLOCK_LOW_LIMIT C)], # memblock.h:343
    [
        qr{^Documented in:},
        {doc => { not => qr{/} }}
    ],
    MUST_SUCCEED);

# Specific cases from #134

# Like regmap_update_bits_base()
run_produces_ok('ident query (existent, function, documented in C file, nonstandard doc comment, #134)',
    [$tenv->query_py, qw(v5.4 ident issue134_function1 C)],
    [
        qr{^Documented in:},
        {doc => qr{\bissue134\.c.+\b9\b}},
    ],
    MUST_SUCCEED);

# Like wait_for_completion()
run_produces_ok('ident query (existent, function, documented in C file, nonstandard doc comment, #134)',
    [$tenv->query_py, qw(v5.4 ident issue134_function2 C)],
    [
        qr{^Documented in:},
        {doc => qr{\bissue134\.c.+\b25\b}},
    ],
    MUST_SUCCEED);

# Like v4l2_fwnode_endpoint_parse()
run_produces_ok('ident query (existent, prototype, documented in C file), #134',
    [$tenv->query_py, qw(v5.4 ident issue134_function3 C)],
    [
        qr{^Documented in:},
        {doc => qr{\bissue134\.c.+\b38\b}},
    ],
    MUST_SUCCEED);

done_testing;
