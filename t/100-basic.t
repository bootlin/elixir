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

use Cwd qw(abs_path);
use File::Path qw(remove_tree);
use File::Spec;
use File::Temp 0.14 qw(tempdir);

use Test::More;

use TestHelpers;

# ===========================================================================
# Main

# Set up
my $tree_src_dir = sibling_abs_path('tree');
my $db_dir = sibling_abs_path('db');        # the db dir is .gitignored

{   # Remove any existing DB dir
    my $ignore;
    remove_tree($db_dir, {error => \$ignore});
}

# Check programs
my $script_sh = find_program('script.sh');
my $update_py = find_program('update.py');
my $query_py = find_program('query.py');

ok_or_die( (-f $script_sh && -r _ && -x _), 'script.sh executable',
    "Could not find executable script.sh at $script_sh");
ok_or_die( (-f $update_py && -r _ && -x _), 'update.py executable',
    "Could not find executable update.py at $update_py");
ok_or_die( (-f $query_py && -r _ && -x _), 'query.py executable',
    "Could not find executable query.py at $query_py");

# Copy tree/ into a temporary Git repository, since script.sh requires
# it be run in a Git repo.

my $tempdir = tempdir(CLEANUP => 1);
my $tempdir_path = abs_path($tempdir);
diag "Using temporary directory $tempdir_path";
run_program('bash', '-c', "cd \"$tempdir\" && git init") or die("git init failed");

run_program('bash', '-c', "tar cf - -C \"$tree_src_dir\" . | tar xf - -C \"$tempdir\"")
    or die("Could not copy files into $tempdir");

my @gitdir = ('-C', $tempdir_path);

run_program('git', @gitdir, 'add', '.') or die("git add failed");
run_program('git', @gitdir, 'commit', '-am', 'Initial commit')
    or die("git commit failed");
run_program('git', @gitdir, 'tag', 'v5.4') or die("git tag failed");

$ENV{LXR_REPO_DIR} = $tempdir;
$ENV{LXR_DATA_DIR} = $db_dir;

# Check for tags in `script.sh list-tags`, as a sanity check before
# building the test DB
my @tags = `$script_sh list-tags`;
die("Could not list tags: $! ($?)") if $?;
ok_or_die( @tags == 1, 'One tag present', "Not one tag (@{[scalar @tags]})");
ok_or_die( $tags[0] =~ /^v5.4$/, 'Found the correct tag', 'Not the tag we expected');

# Make the new database
ok_or_die( mkdir($db_dir), "Created $db_dir",
    "Could not create $db_dir");

ok_or_die( run_program($update_py), 'update.py succeeded',
    'Could not create database');

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
    1);

run_produces_ok('ident query (existent)',
    [$query_py, qw(v5.4 ident i2c_acpi_notify)],
    [qr{^Symbol Definitions:}, qr{^Symbol References:},
        qr{drivers/i2c/i2c-core-acpi\.c.+\b402\b.+\bfunction\b},    # def
        qr{drivers/i2c/i2c-core-acpi\.c.+\b402,439}                 # refs
    ],
    1);

# Spot-check some files

run_produces_ok('file query (nonexistent)',
    [$query_py, qw(v5.4 file /SOME_NONEXISTENT_FILENAME_XYZZY_PLUGH)],
    [{not => qr{\S}}]);

run_produces_ok('file query (existent), .h',
    [$query_py, qw(v5.4 file /drivers/i2c/i2c-dev.c)],
    [qr{\S}],
    1);

run_produces_ok('file query (existent), .c',
    [$query_py, qw(v5.4 file /drivers/i2c/i2c-dev.c)],
    [qr{i2c-dev\.c}, qr{\bVogl\b}],
    1);

run_produces_ok('file query (existent), .h',
    [$query_py, qw(v5.4 file /drivers/i2c/i2c-core.h)],
    [qr{i2c-core\.h}, qr{\bWe\b}],
    1);

#system('bash'); # Uncomment this if you want to interact with the test repo

done_testing;
