#!/usr/bin/env perl
# TestHelpers.pm: Common routines for use in tests.
# See license information at end of file.
#
# For a cleaner view of the documentation, run
#   perldoc TestHelpers.pm
# (on Ubuntu, you may need to install the perl-doc package first.)
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file uses core Perl modules only.

=head1 NAME

TestHelpers - Common routines for use in tests

=head1 SYNOPSIS

C<use TestHelpers;>, and all the functions below will be exported.

=cut

package TestHelpers;

use strict;
use warnings;
use autodie;    # note: still need to check system() calls manually

use Cwd qw(abs_path);
use File::Spec;
use File::Temp 0.14 qw(tempdir);
use FindBin;
use IO::Select;
use IPC::Open3;
use Symbol;

use Test::More;

# Automatically export all the functions below
use parent 'Exporter';
our @EXPORT;
BEGIN { @EXPORT = qw(sibling_abs_path find_program run_program ok_or_die
    run_produces_ok MUST_SUCCEED); }

# ===========================================================================

=head1 CONSTANTS

=head2 MUST_SUCCEED

True.  So that calls to L</run_produces_ok> will be more self-explanatory.

=cut

use constant MUST_SUCCEED => !!1;

=head1 FUNCTIONS

These are helper routines that generally perform specific tasks.

=head2 sibling_abs_path

Return the absolute path of a file or directory in the same directory as
this file.  Usage:

    $path = sibling_abs_path('name');

=cut

sub sibling_abs_path {
    return File::Spec->rel2abs(File::Spec->catfile($FindBin::Bin, @_));
}

=head2 find_program

Looks for a program in the parent directory of this script.
Usage:

    $path = find_program('program name')

=cut

sub find_program {
    my $program = shift;

    my ($vol, $directories, $file) = File::Spec->splitpath($FindBin::Bin, 1);   # 1 => is a dir

    # Go up to the parent of the directory holding this file
    my @dirs = File::Spec->splitdir($directories);
    die "Cannot run from the root directory" unless @dirs >= 2;
    pop @dirs;
    $directories = File::Spec->catdir(@dirs);

    return File::Spec->catpath($vol, $directories, $program);
} #find_program()

=head2 run_program

Print a command, then run it.  Returns true if system() and the command
succeed, false otherwise.  Usage:

    $ok = run_program('program', 'arg1', ...)

=cut

sub run_program {
    diag "Running @_";
    my $status = system(@_);
    if ($status == -1) {
        diag "failed to execute $_[0]: $!";
    }
    elsif ($status & 127) {
        diag sprintf "$_[0] died with signal %d, %s coredump\n",
            ($status & 127),  ($status & 128) ? 'with' : 'without';
    }
    else {
        diag sprintf "$_[0] exited with value %d\n", $status >> 8;
    }

    return($status == 0);
} #run_program()

=head2 ok_or_die

Run a test, but die if it fails.  Usage:

    ok_or_die( <some condition>, 'description', 'what to print if it dies' )

=cut

sub ok_or_die {
    my ($cond, $msg, $err_msg) = @_;
    my $line = (caller)[2];
    my $retval = eval <<EOT;    # Make the error message report the caller's line number
#line $line
    ok(\$cond, \$msg);
EOT
    die($err_msg) unless $retval;
    return $retval;
} #ok_or_die()

=head2 run_produces_ok

Run a program and check whether it produces expected output.
Usage:

    run_produces_ok($desc, \@program_and_args, \@expected_regexes,
                    <optional> $mustSucceed)

The test passes if each regex in C<@expected_regexes> matches at least one
line in the output of C<@program_and_args>, and if each C<< { not => regex } >>
in C<@expected_regexes> is NOT found in that output.
If C<$mustSucceed> is true, also tests for exit status 0 and empty stderr.

=cut

sub run_produces_ok {
    my ($desc, $lrProgram, $lrRegexes, $mustSucceed) = @_;

    # Run program and capture stdout and stderr
    my ($in , $out, $err);      # Filehandles
    $err = Symbol::gensym;
    diag "Running @$lrProgram";
    my $pid = open3($in, $out, $err, @$lrProgram);

    my (@outlines, @errlines);  # Captured output
    my $s = IO::Select->new;
    $s->add($out);
    $s->add($err);

    while(my @ready = $s->can_read) {
        for my $fh (@ready) {

            if(eof($fh)) {
                $s->remove($fh);
                next;
            }

            if($fh == $out) {
                push @outlines, scalar readline $fh;
            } else {
                push @errlines, scalar readline $fh;
            }
        }
    }

    waitpid $pid, 0;
    my $exit_status = $? >> 8;

    # Basic checks
    if($mustSucceed) {
        cmp_ok($exit_status, '==', 0, "$desc: exit status 0");
        cmp_ok(@errlines, '==', 0, "$desc: stderr empty");
    }

    # Check regexes
    for my $entry (@$lrRegexes) {

        if(ref $entry eq 'Regexp') {
            ok( (grep { m{$entry} } @outlines), "$desc: output includes $entry" );

        } elsif(ref $entry eq 'HASH' && ref $entry->{not} eq 'Regexp') {
            my $re = $entry->{not};
            ok( !(grep { m{$re} } @outlines), "$desc: output excludes $re" );

        } else {
            die "Invalid entry $entry";
        }
    } #foreach $entry

} #run_produces_ok()

1;
__END__


=head1 AUTHOR

Christopher White, C<< <cwhite@d3engineering.com> >>

=head1 COPYRIGHT

Copyright (c) 2020 D3 Engineering, LLC.

Elixir is free software; you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Elixir is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Elixir.  If not, see <http://www.gnu.org/licenses/>.

=cut
