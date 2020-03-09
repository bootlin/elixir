#!/usr/bin/env perl
# 100-basic.t: Test basic elixir functions against the files in tree/ .
#
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

use strict;
use warnings;
use autodie;    # note: still need to check system() calls manually

use FindBin '$Bin';
use lib $Bin;

use File::Spec;

use Test::More;

use TestEnvironment;
use TestHelpers;

# ===========================================================================
# Main

# Set up
my $tree_src_dir = sibling_abs_path('tree');
my $db_dir = sibling_abs_path('db');        # the db dir is .gitignored

my $tenv = TestEnvironment->new;

# Check programs
my $script_sh = $tenv->script_sh;
my $update_py = $tenv->update_py;
my $query_py = $tenv->query_py;

ok_or_die( (-f $script_sh && -r _ && -x _), 'script.sh executable',
    "Could not find executable script.sh at $script_sh");
ok_or_die( (-f $update_py && -r _ && -x _), 'update.py executable',
    "Could not find executable update.py at $update_py");
ok_or_die( (-f $query_py && -r _ && -x _), 'query.py executable',
    "Could not find executable query.py at $query_py");

$tenv->build_repo($tree_src_dir);
$tenv->update_env;  # Set LXR_REPO_DIR

# Check for tags in `script.sh list-tags`, as a sanity check before
# building the test DB
my @tags = `$script_sh list-tags`;
die("Could not list tags: $! ($?)") if $?;
ok_or_die( @tags == 1, 'One tag present', "Not one tag (@{[scalar @tags]})");
ok_or_die( $tags[0] =~ /^v5.4$/, 'Found the correct tag', 'Not the tag we expected');

$tenv->build_db($db_dir);
$tenv->update_env;  # Set LXR_DATA_DIR

ok_or_die( -d $db_dir, 'database dir exists',
    "Database dir $db_dir not present");

# Make sure the database has the files we expect
ok( (-r File::Spec->catfile($db_dir, $_)), "$_ exists" )
    foreach qw(blobs.db definitions.db filenames.db hashes.db references.db
                variables.db versions.db);

# Spot-check some identifiers

run_produces_ok('ident query (nonexistent)',
    [$query_py, qw(v5.4 ident SOME_NONEXISTENT_IDENTIFIER_XYZZY_PLUGH)],
    [qr{^Symbol Definitions:}, qr{^Symbol References:}, qr{^\s*$}],
    MUST_SUCCEED);

run_produces_ok('ident query (existent)',
    [$query_py, qw(v5.4 ident i2c_acpi_notify)],
    [qr{^Symbol Definitions:}, qr{^Symbol References:},
        qr{drivers/i2c/i2c-core-acpi\.c.+\b402\b.+\bfunction\b},    # def
        qr{drivers/i2c/i2c-core-acpi\.c.+\b402,439}                 # refs
    ],
    MUST_SUCCEED);

# Spot-check some files

run_produces_ok('file query (nonexistent)',
    [$query_py, qw(v5.4 file /SOME_NONEXISTENT_FILENAME_XYZZY_PLUGH)],
    [{not => qr{\S}}]);

run_produces_ok('file query (existent), .h',
    [$query_py, qw(v5.4 file /drivers/i2c/i2c-dev.c)],
    [qr{\S}],
    MUST_SUCCEED);

run_produces_ok('file query (existent), .c',
    [$query_py, qw(v5.4 file /drivers/i2c/i2c-dev.c)],
    [qr{i2c-dev\.c}, qr{\bVogl\b}],
    MUST_SUCCEED);

run_produces_ok('file query (existent), .h',
    [$query_py, qw(v5.4 file /drivers/i2c/i2c-core.h)],
    [qr{i2c-core\.h}, qr{\bWe\b}],
    MUST_SUCCEED);

#system('bash'); # Uncomment this if you want to interact with the test repo

done_testing;
