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
TestHelpers also turns on L<strict> and L<warnings>.

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

# Automatically export all the functions listed in @EXPORT.  The functions
# in @EXPORT_OK can be exported on request.
use parent 'Exporter';
our (@EXPORT, @EXPORT_OK, %EXPORT_TAGS);
BEGIN {
    @EXPORT = qw(sibling_abs_path find_program run_program ok_or_die
                run_produces_ok MUST_SUCCEED);
    @EXPORT_OK = qw(line_mark_string);
    %EXPORT_TAGS = (
        all => [@EXPORT, @EXPORT_OK],
    );
}

# Forwards for internal functions
sub line_mark_string;

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
    my (undef, $filename, $line) = caller;
    my $retval = eval line_mark_string 1, <<EOT;    # Make the error message report the caller's line number
    ok(\$cond, \$msg);
EOT
    die($err_msg) unless $retval;
    return $retval;
} #ok_or_die()

=head2 run_produces_ok

Run a program and check whether it produces expected output.
Usage:

    run_produces_ok($desc, \@program_and_args, \@expected_regexes,
                    <optional> $mustSucceed, <optional> $printOutput)

The test passes if each regex in C<@expected_regexes> matches at least one
line in the output of C<@program_and_args>, and if each C<< { not => regex } >>
in C<@expected_regexes> is NOT found in that output.
If C<$mustSucceed> is true, also tests for exit status 0 and empty stderr.
If C<$printOutput> is true, prints the output of C<@program_and_args>.

=cut

sub run_produces_ok {
    my ($desc, $lrProgram, $lrRegexes, $mustSucceed, $printOutput) = @_;

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

    if ($printOutput) {
        diag "@outlines";
    }

    # Basic checks
    if($mustSucceed) {
        eval line_mark_string 1, <<'EOT';
        cmp_ok($exit_status, '==', 0, "$desc: exit status 0");
        cmp_ok(@errlines, '==', 0, "$desc: stderr empty");
EOT
    }

    # Check regexes
    for my $entry (@$lrRegexes) {

        if(ref $entry eq 'Regexp') {
            eval line_mark_string 1,
            q(ok( (grep { m{$entry} } @outlines), "$desc: output includes $entry" ));

        } elsif(ref $entry eq 'HASH' && ref $entry->{not} eq 'Regexp') {
            my $re = $entry->{not};
            eval line_mark_string 1,
            q(ok( !(grep { m{$re} } @outlines), "$desc: output excludes $re" ));

        } else {
            die "Invalid entry $entry";
        }
    } #foreach $entry

} #run_produces_ok()

=head1 INTERNAL FUNCTIONS

These are ones you probably won't need to call.

=head2 _croak

Lazy L<Carp/croak>

=cut

sub _croak {
    require Carp;
    goto &Carp::croak;
}

=head2 line_mark_string

Add a C<#line> directive to a string.  Usage:

To use the caller's filename and line number:

    my $str = line_mark_string <<EOT ;
    $contents
    EOT

To use a filename and line number from higher in the call stack:

    my $str = line_mark_string $level, <<EOT ;
    $contents
    EOT

To use a specified filename and line number:

    my $str = line_mark_string __FILE__, __LINE__, <<EOT ;
    $contents
    EOT

In the first and second forms, information from C<caller> will be used for the
filename and line number.

In the first and third forms, the C<#line> directive will point to the line
after the C<line_mark_string> invocation, i.e., the first line of <C$contents>.
Generally, C<$contents> will be source code, although this is not required.

C<$contents> must be defined, but can be empty.

=cut

sub line_mark_string {
    my ($contents, $filename, $line);

    if(@_ == 1) {
        $contents = $_[0];
        (undef, $filename, $line) = caller;
        ++$line;
    } elsif(@_ == 2) {
        (undef, $filename, $line) = caller($_[0]);
        $contents = $_[1];
    } elsif(@_ == 3) {
        ($filename, $line, $contents) = @_;
        ++$line;
    } else {
        _croak "Invalid invocation";
    }

    _croak "Need text" unless defined $contents;
    die "Couldn't get location information" unless $filename && $line;

    $filename =~ s/"/-/g;

    return <<EOT;
#line $line "$filename"
$contents
EOT
} #line_mark_string()

=head2 import

Set up.  Called automatically.

=cut

sub import {
    __PACKAGE__->export_to_level(1, @_);
    strict->import;
    warnings->import;
} #import()

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
