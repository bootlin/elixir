#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Copyright (C) 2026 The Elixir contributors
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

"""Split Python source into the token stream used by script.sh.

Reads a source file on stdin and writes alternating separator and identifier
lines. Newlines inside separators are encoded as \\001 so the indexer can
count lines, and concatenating the pieces reproduces the original file.
Comments and string literals stay in the separator text, so names mentioned
only there are not references. Names inside f-string expressions are emitted
when the running Python's tokenizer exposes them.
"""

import sys
import tokenize
from io import StringIO


def _line_starts(src):
    starts = [0]
    for index, char in enumerate(src):
        if char == '\n':
            starts.append(index + 1)
    return starts


def _offset(starts, row, col):
    return starts[row - 1] + col


def tokenize_source(src):
    """Return the Elixir token stream for a Python source string."""
    starts = _line_starts(src)
    out = []
    last = 0
    try:
        reader = StringIO(src).readline
        for tok in tokenize.generate_tokens(reader):
            if tok.type == tokenize.ENDMARKER:
                break
            if tok.type != tokenize.NAME or not tok.string.isidentifier():
                continue
            start = _offset(starts, tok.start[0], tok.start[1])
            end = _offset(starts, tok.end[0], tok.end[1])
            if start < last or end > len(src):
                continue
            out.append(src[last:start].replace('\n', '\001'))
            out.append('\n')
            out.append(tok.string)
            out.append('\n')
            last = end
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # Keep a broken file viewable, without inventing identifiers.
        return src.replace('\n', '\001')

    out.append(src[last:].replace('\n', '\001'))
    return ''.join(out)


def main():
    raw = sys.stdin.buffer.read()
    try:
        src = raw.decode('utf-8')
    except UnicodeDecodeError:
        src = raw.decode('utf-8', errors='surrogateescape')
    text = tokenize_source(src)
    out = text.encode('utf-8', errors='surrogateescape')
    if not out.endswith(b'\n'):
        out += b'\n'
    sys.stdout.buffer.write(out)


if __name__ == '__main__':
    main()
