#!/usr/bin/env perl
# t/interact.pl: Open a shell on a DB of the files in tree/ .
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

use Cwd;
use TestEnvironment;
use TestHelpers;

# ===========================================================================
# Main

my $pwd = getcwd;

# This block is all that's required to set up for a test.
my $tenv = TestEnvironment->new;
$tenv->build_repo(sibling_abs_path('tree'));	# dies on error
eval { $tenv->build_db; };
warn "Could not update database: $@" if $@;
$tenv->update_env;

print($tenv->report);

# Make some convenient symlinks
chdir($tenv->lxr_repo_dir);
system(qw(ln -s), $tenv->script_sh, 'script.sh') == 0
    or warn "error creating ./script.sh: $? $!";
system(qw(ln -s), $tenv->update_py, 'update.py') == 0
    or warn "error creating ./update.py: $? $!";
system(qw(ln -s), $tenv->query_py, 'query.py') == 0
    or warn "error creating ./query.py: $? $!";
system(qw(ln -s), $tenv->web_py, 'web.py') == 0
    or warn "error creating ./web.py: $? $!";
system(qw(ln -s), $tenv->find_doc, 'find-file-doc-comments.pl') == 0
    or warn "error creating ./find-file-doc-comments.pl: $? $!";

print("Exit when done, and the repository and database will be removed.\n");
my $retval = system($ENV{SHELL} || 'sh');

# Don't stay in the temp dir --- the dir can't be removed if we are there.
chdir $pwd;

exit $retval>>8;
