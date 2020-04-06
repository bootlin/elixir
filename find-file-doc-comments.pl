#!/usr/bin/env perl
# find-file-doc-comments.pl: Find the doc comments for a file.
# Usage: find-file-doc-comments.pl <C source file name>
# By Christopher White <cwhite@d3engineering.com>
# Copyright (c) 2019 D3 Engineering, LLC.
# Licensed AGPLv3

use 5.010001;
use strict;
use warnings FATAL => qw(uninitialized);
use autodie;

my $VERBOSE = $ENV{V};

exit main(@ARGV);

sub main {
    die "Need a filename" unless @_;
    say "Processing file $_[0]" if $VERBOSE;

    # Do `script.sh parse-defs` on the file
    my @ctags = qx{ ctags -x --c-kinds=+p-m --language-force=C "$_[0]" |
            grep -av "^operator " |
            awk '{print \$1" "\$2" "\$3}' };
    die "Could not get ctags: $!" if $!;
    print "No ctags results" if $VERBOSE && !@ctags;
    return 0 unless @ctags;

    # Make a list of [name, type, line] arrays
    my @ctags_parsed = map { [split] } @ctags;

    # Flip it around to index functions by line
    my %function_lines;
    for my $tag (@ctags_parsed) {
        next unless $tag->[1] eq 'function';
        $function_lines{$tag->[2]} = $tag->[0];
    }

    if($VERBOSE) {
        for my $tag (@ctags_parsed) {
            say $tag->[2], ': ', $tag->[0], ' is a(n) ', $tag->[1];
        }
    }

    # Read the source file
    open my $fh, '<', $_[0];
    my @source_lines = (undef, <$fh>);
        # undef => indices in @source_lines match ctags's 1-based linenos
    close $fh;

    # Work backwards through the file and look for doc comments
    my %doc_comments;

    my $doc_comment_opener = qr{^\s*\/\*\*(?:\s|$)};    # Start of doc comment

    for(my $lineno = $#source_lines ; $lineno >= 1 ; --$lineno) {
        next unless exists $function_lines{$lineno};
        my $func_name = $function_lines{$lineno};
        print "Checking for $func_name @ $lineno\n" if $VERBOSE;

        my $this_doc_comment_header =
            qr{^\s+\*\s+\Q$func_name\E(?:\s|\(|$)};
        print "  Regex is -$this_doc_comment_header-\n" if $VERBOSE;
        --$lineno;
        print "  Line $lineno is: $source_lines[$lineno]\n" if $VERBOSE;

        # Find the last line that could be a doc-comment header
        # for this function.
        while($lineno && $source_lines[$lineno] =~
            qr{
                    ^\s*$               # Empty line
                |   ^\s+\*\/            # End of comment
                |   ^\s+\*(?:\s|$)      # Continuation of comment
                |   $this_doc_comment_header
            }x) {
            print "$source_lines[$lineno] passed\n" if $VERBOSE;
            --$lineno;
        }
        ++$lineno;  # Check the last line that matched,
                    # because we may have just skipped past $this_doc_comment_header

        # Is it actually a header for this function?
        print "Checking $source_lines[$lineno] for header\n" if $VERBOSE;
        next unless $source_lines[$lineno] =~ $this_doc_comment_header;

        # We have found a header.  Confirm it's a doc comment.
        --$lineno;
        next unless $lineno > 0 && $source_lines[$lineno] =~ $doc_comment_opener;
        print "  * Match\n" if $VERBOSE;

        # We have found a doc comment for this function!  Record it.
        push @{$doc_comments{$func_name}}, $lineno;
    }

    # Report the doc comments for each function
    for my $funcname (keys %doc_comments) {
        my $comment_lines = $doc_comments{$funcname};
        print "$funcname $_\n" foreach @$comment_lines;
    }

    return 0;
}
