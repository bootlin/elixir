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
} #BEGIN

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
} #sibling_abs_path()

=head2 find_program

Looks for a program in the parent directory of this script.
Usage:

    $path = find_program(['subdir', ]'program name')

=cut

sub find_program {
    my $pgm_file = pop;  # Last arg
    my @pgm_dirs = @_;  # Any args before the last are additional dirs.

    my ($my_vol, $my_dirs, undef) = File::Spec->splitpath($FindBin::Bin, 1);   # 1 => is a dir

    # Go up to the parent of the directory holding this file
    my @my_dirs = File::Spec->splitdir($my_dirs);
    die "Cannot run from the root directory" unless @my_dirs >= 2;
    pop @my_dirs;
    my $dest_dirs = File::Spec->catdir(@my_dirs, @pgm_dirs);

    return File::Spec->catpath($my_vol, $dest_dirs, $pgm_file);
} #find_program()

=head2 run_program

Print a command, then run it.  Can be used three ways:

=over

=item In void context

Returns if system() and the command succeed, dies otherwise.  Usage:

    run_program('program', 'arg1', ...);

=item In scalar context

Returns true if system() and the command succeed, false otherwise.  Usage:

    my $ok = run_program('program', 'arg1', ...);

=item In list context

Returns the exit status, stdout, and stderr.  Usage:

    my ($exit_status, $lrStdout, $lrStderr) = run_program('program', 'arg1', ...);
        # Returns the shell exit status, stdout text, and stderr text.

C<$lrStdout> and C<$lrStderr> are references to the lists of output lines
on the respective handles.

C<$exit_status> is C<128+signal> if the process was killed by C<signal>,
for consistency with bash (L<https://tldp.org/LDP/abs/html/exitcodes.html>).

=back

=cut

sub _run_and_capture;   # forward

sub run_program {
    diag "Running @_";

    if(wantarray) {
        goto &_run_and_capture;
    }

    my $errmsg;

    my $status = system(@_);

    if ($status == -1) {
        $errmsg = "failed to execute $_[0]: $!";
    }
    elsif ($status & 127) {
        $errmsg = sprintf "$_[0] died with signal %d, %s coredump\n",
            ($status & 127),  ($status & 128) ? 'with' : 'without';
    }
    elsif($status != 0) {
        $errmsg = sprintf "$_[0] exited with value %d\n", $status >> 8;
    }
    else {
        diag "$_[0] reported success";
    }

    if($errmsg) {
        die $errmsg unless defined wantarray;
        diag $errmsg;
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

The test passes if each condition in C<@conditions> is true.
If C<$mustSucceed> is true, also tests for exit status 0 and empty stderr.
If C<$printOutput> is true, prints the output of C<@program_and_args>.

=head3 Conditions that can be used any time

=over

=item *

A regex: true if the regex matches at least one line in the output of
C<@program_and_args>

=item *

C<< { not => regex } >>: true if the regex is NOT found in any line of
the output of C<@program_and_args>.

=back

=head3 Conditions for the output of C<query.py>

=over

=item *

C<< { def => regex } >>: true if the regex matches at least one line in
the "Symbol Definitions" section of the output of C<@program_and_args>.

=item *

C<< { ref => regex } >>: true if the regex matches at least one line in
the "Symbol References" section of the output of C<@program_and_args>.

=item *

C<< { doc => regex } >>: true if the regex matches at least one line in
the "Documented in" section of the output of C<@program_and_args>.

=back

=cut

# _run_and_capture: run a program and return its exit status and output.
# Usage:
#   my ($exit_status, \@stdout, \@stderr) = run_program('program', 'arg1', ...);

sub _run_and_capture {
    my ($in , $out, $err);      # Filehandles
    $err = Symbol::gensym;

    diag "Running @_";
    my $pid = open3($in, $out, $err, @_);

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
    my $exit_status = $?;

    $exit_status = ($exit_status & 127) + 128 if $exit_status & 127;   # Killed by signal

    return ($exit_status, \@outlines, \@errlines);
} #_run_and_capture()

sub run_produces_ok {
    my ($desc, $lrProgram, $lrRegexes, $mustSucceed, $printOutput) = @_;

    my ($exit_status, $outlines, $errlines) = _run_and_capture(@$lrProgram);
    my @outlines = @$outlines;
    my @errlines = @$errlines;

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
    my %query_py_output;    # filled in only if we see a def/ref/doc
    for my $entry (@$lrRegexes) {
        my ($re, $negated, $source) = _parse_condition($entry);

        # Parse query.py output if we need it and haven't done so
        %query_py_output = _parseq(@outlines)
            if $source ne 'output' && !%query_py_output;

        # Build a line of test code to run
        my $test = 'ok( ';
        $test .= '!' if $negated;
        $test .= '(grep { m{$re} } ';
        if($source eq 'output') {
            $test .= '@outlines';
        } else {
            $test .= '@{$query_py_output{' . $source . '}}';
        }
        $test .= '), "$desc: ' . $source;
        $test .= ($negated ? ' excludes ' : ' includes ') . "\Q$re\E" . '");';

        # Run it
        #diag "Running $test";
        eval line_mark_string 1, $test;
    } #foreach $entry

} #run_produces_ok()

=head1 INTERNAL FUNCTIONS

These are ones you probably won't need to call.

=head2 _parseq

Parse the output of query.py.  Usage:

    %parsed = _parseq(@lines_of_output);

=cut

sub _parseq {
    my %retval = ( def => [], ref => [], doc => [] );
    my $list;
    foreach(@_) {
        chomp;
        if($_ eq 'Symbol Definitions:') {
            $list = 'def';
            next;
        } elsif($_ eq 'Symbol References:') {
            $list = 'ref';
            next;
        } elsif($_ eq 'Documented in:') {
            $list = 'doc';
            next;
        }

        #diag "Adding `$_' to list $list";
        push @{$retval{$list}}, $_;
    }
    return %retval;
} #_parseq()

=head2 _parse_condition

Parse a condition for L</run_produces_ok>.  Usage:

    ($regex, $negated, $source) = _parse_condition($entry[, $source]);

=cut

sub _parse_condition {
    my ($entry, $source_in) = @_;
    my ($regex, $negated, $source);     # Return values

    # Basic cases
    if(ref $entry eq 'Regexp') {
        return ($entry, 0, $source_in || 'output');
    } elsif(ref $entry eq 'HASH' && ref $entry->{not} eq 'Regexp') {
        return ($entry->{not}, 1, $source_in || 'output');
    }

    # Sub-keys: chain
    if(ref $entry eq 'HASH' && scalar keys %{$entry} == 1) {
        return _parse_condition((values %{$entry})[0], (keys %{$entry})[0]);
    }

    # If we get here, we don't know how to handle it
    die "Invalid entry $entry";
} #_parse_condition()


=head2 _croak

Lazy invoker for L<Carp/croak>.

=cut

sub _croak {
    require Carp;
    goto &Carp::croak;
} #_croak()

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
