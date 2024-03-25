#!/usr/bin/env perl
# find-file-doc-comments.pl: Find the doc comments for a file.
# Usage: find-file-doc-comments.pl <C source file name>

#  This file is part of Elixir, a source code cross-referencer.
#
#  By Christopher White <cwhite@d3engineering.com>
#  Copyright (c) 2019--2020 D3 Engineering, LLC.
#
#  Elixir is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Elixir is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Elixir.  If not, see <http://www.gnu.org/licenses/>.

use 5.010001;
use strict;
use warnings;
use autodie;

my $VERBOSE = $ENV{V};

exit main(@ARGV);

sub main {
    die "Need a filename" unless @_;
    my $filename = shift;
    die "Could not read $filename" unless -r $filename;
    say "Processing file $filename" if $VERBOSE;

    # Fatalize all warnings, and log which file triggered the warning.
    local $SIG{__WARN__} = sub {
        die "While processing $filename: $_[0]\n";
    };

    # Do `script.sh parse-defs` on the file
    my @ctags = qx{ ctags -x --c-kinds=+p-m --language-force=C "$filename" |
            grep -av "^operator " |
            awk '{print \$1" "\$2" "\$3}' };
    die "Could not get ctags: $!" if $!;
    say "No ctags results" if $VERBOSE && !@ctags;
    return 0 unless @ctags;

    # Make a list of [name, type, line] arrays
    my @ctags_parsed = map { [split] } @ctags;

    # Flip it around to index functions and types by line.  Don't index anything
    # by name, since there can be multiple names with different types/lines (#186).
    my %definition_lines;
    my %definition_types;
    for my $tag (@ctags_parsed) {
        $definition_lines{$tag->[2]} = $tag->[0];
        $definition_types{$tag->[2]} = $tag->[1] // '<none>';
    }

    if($VERBOSE) {
        for my $tag (sort { $a->[2] <=> $b->[2] } @ctags_parsed) {
            say $tag->[2], ': ', $tag->[0], ' is a(n) ', $tag->[1];
        }
    }

    # Read the source file
    open my $fh, '<', $filename;
    my @source_lines = (undef, <$fh>);
        # undef => indices in @source_lines match ctags's 1-based linenos
    close $fh;

    # Work backwards through the file and look for doc comments
    my %doc_comments;

    my $doc_comment_opener = qr{^\h*\/\*\*(?:\h|$)};    # Start of doc comment
    my $comment_leader = qr{\h+\*\h+(?:(?:struct|enum|union|typedef)\h+)?};

    for(my $lineno = $#source_lines ; $lineno >= 1 ; --$lineno) {
        next unless exists $definition_lines{$lineno};
        my $definition_name = $definition_lines{$lineno};
        my $definition_type = $definition_types{$lineno};
        say "\nChecking $definition_type $definition_name @ $lineno" if $VERBOSE;

        # Comment header: be liberal in what we accept.  For example, do not
        # check the type of the definition/declaration against the type in
        # the comment header.  I don't think this will be a problem.
        my $this_doc_comment_header =
            qr{^$comment_leader\Q$definition_name\E(?:\h|\(|:|$)};
        say "  Regex is -$this_doc_comment_header-" if $VERBOSE;

        # Make sure we get back past the first line of multiline definitions
        if($definition_type eq 'macro') {
            --$lineno while $lineno && $source_lines[$lineno] !~ /^\h*#\h*define/;
        } elsif($definition_type eq 'function') {
            # Try to handle the case of "int\nfoo()"
            if($source_lines[$lineno] =~ /^\h*\Q$definition_name\E\b/) {
                --$lineno while $lineno && $source_lines[$lineno] =~ /^[a-z_]/i;
            }
        }

        # Assume cflags gave us the first line of the definition, or we got
        # back to it manually.  Move to the first line that might be a doc comment.
        --$lineno;

        # If we ran off the beginning of the file, there's no doc comment.
        next if $lineno <= 0;

        # TODO make sure we're not still in the definition.
        # E.g., memblock.h:for_each_mem_range().  The defintion is reported
        # on the second line of the #define, not the first line.

        say "  Starting search for docs at line $lineno" if $VERBOSE;

        # Find the last line that could be a doc-comment header
        # for this function.
        while($lineno && $source_lines[$lineno] =~
            qr{
                    ^\h*$               # Empty line
                |   ^\h+\*\/            # End of comment
                |   ^\h+\*(?:\h|$)      # Continuation of comment
                |   $this_doc_comment_header
            }x) {
            if($VERBOSE) {
                my $line = $source_lines[$lineno];
                chomp $line;
                say "  skipped $lineno '$line'";
            }
            --$lineno;
        }
        ++$lineno;  # Check the last line that matched,
                    # because we may have just skipped past $this_doc_comment_header

        # Is it actually a header for this function?
        say "  Checking line $lineno for header" if $VERBOSE;
        next unless $source_lines[$lineno] =~ $this_doc_comment_header;

        # We have found a header.  Confirm it's a doc comment.
        --$lineno;
        next unless $lineno > 0 && $source_lines[$lineno] =~ $doc_comment_opener;
        say "  * Match" if $VERBOSE;

        # We have found a doc comment for this function!  Record it.
        push @{$doc_comments{$definition_name}}, $lineno;
    } # foreach line in reverse order

    # Report the doc comments for each function
    for my $definition_name (keys %doc_comments) {
        my $comment_lines = $doc_comments{$definition_name};
        say "$definition_name $_" foreach @$comment_lines;
    }

    return 0;
} #main
