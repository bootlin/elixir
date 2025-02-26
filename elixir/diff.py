from typing import Generator, Optional, Tuple, List
from pygments.formatters import HtmlFormatter

from elixir.query import DiffEntry

PygmentsSource = Generator[Tuple[int, str], None, None]

# Wraps pygments HtmlFormatter to create a single diff pane, depending on `left` argument
class DiffFormater(HtmlFormatter):
    def __init__(self, diff: List[DiffEntry], left: bool, *args, **kwargs):
        self.diff = diff
        self.left = left
        super().__init__(*args[2:], **kwargs)

    # Wraps pygments line (1 if increase line number, html) in span tag with css_class
    def mark_line(self, line: Tuple[int, str], css_class: str) -> PygmentsSource:
        yield line[0], f'<span class="{css_class}">{line[1]}</span>'

    # Wraps num pygments lines from source in span tag with css_class
    def mark_lines(self, source: PygmentsSource, num: int, css_class: str) -> PygmentsSource:
        i = 0
        while i < num:
            try:
                t, line = next(source)
            except StopIteration:
                break
            if t == 1:
                yield t, f'<span class="{css_class}">{line}</span>'
                i += 1
            else:
                yield t, line

    # Yields num empty lines
    def yield_empty(self, num: int) -> PygmentsSource:
        for _ in range(num):
            yield 0, '<span class="diff-line">&nbsp;\n</span>'

    # Returns diff entry, number of the entry after it and the start line
    # of the change in the current pane (left or right).
    def get_next_diff_line(self, diff_num: int, next_diff_line: Optional[int]) \
        -> Tuple[Optional[DiffEntry], int, Optional[int]]:

        next_diff = self.diff[diff_num] if len(self.diff) > diff_num else None

        if next_diff is not None:
            if self.left and next_diff.type in ('-', '+'):
                next_diff_line = next_diff.left_start
            elif next_diff.type in ('-', '+'):
                next_diff_line = next_diff.right_start
            elif self.left and next_diff.type == '=':
                next_diff_line = next_diff.left_start
            elif next_diff.type == '=':
                next_diff_line = next_diff.right_start
            else:
                raise Exception("invalid next diff mode")

        return next_diff, diff_num+1, next_diff_line

    # Wraps Pygments source generator in diff generator
    def wrap_diff(self, source: PygmentsSource):
        next_diff, diff_num, next_diff_line = self.get_next_diff_line(0, None)

        linenum = 0

        while True:
            try:
                line = next(source)
            except StopIteration:
                break

            # If processing line that begins current diff entry
            if linenum == next_diff_line:
                if next_diff is not None:
                    # Yield empty lines in left pane for new lines in right file
                    if self.left and next_diff.type == '+':
                        yield from self.yield_empty(next_diff.right_changed)
                        yield line
                        linenum += 1
                    # Yield green source lines in right pane for new lines in right file
                    elif next_diff.type == '+':
                        yield from self.mark_line(line, 'line-added')
                        yield from self.mark_lines(source, next_diff.right_changed-1, 'line-added')
                        linenum += next_diff.right_changed
                    # Yield red source lines in left pane for removed lines in right file
                    elif self.left and next_diff.type == '-':
                        yield from self.mark_line(line, 'line-removed')
                        yield from self.mark_lines(source, next_diff.right_changed-1, 'line-removed')
                        linenum += next_diff.right_changed
                    # Yield empty lines in right pane for removed lines in right file
                    elif next_diff.type == '-':
                        yield from self.yield_empty(next_diff.right_changed)
                        yield line
                        linenum += 1
                    # Yield highlighted source lines or empty lines in left/right pane for lines changed between files
                    elif next_diff.type == '=':
                        total = max(next_diff.left_changed, next_diff.right_changed)
                        to_print = next_diff.left_changed if self.left else next_diff.right_changed
                        yield from self.mark_line(line, 'line-removed' if self.left else 'line-added')
                        yield from self.mark_lines(source, to_print-1, 'line-removed' if self.left else 'line-added')
                        yield from self.yield_empty(total-to_print)
                        linenum += to_print
                    else:
                        yield line
                        linenum += 1

                next_diff, diff_num, next_diff_line = self.get_next_diff_line(diff_num, next_diff_line)
            # Otherwise just return the line
            else:
                yield line
                linenum += 1

    def wrap(self, source):
        return super().wrap(self.wrap_diff(source))

def format_diff(filename: str, diff, code: str, code_other: str) -> Tuple[str, str]:
    import pygments
    import pygments.lexers
    import pygments.formatters
    from pygments.lexers.asm import GasLexer
    from pygments.lexers.r import SLexer

    try:
        lexer = pygments.lexers.guess_lexer_for_filename(filename, code)
        if filename.endswith('.S') and isinstance(lexer, SLexer):
            lexer = GasLexer()
    except pygments.util.ClassNotFound:
        lexer = pygments.lexers.get_lexer_by_name('text')

    lexer.stripnl = False

    formatter = DiffFormater(
        diff,
        True,
        # Adds line numbers column to output
        linenos='inline',
        # Wraps line numbers in link (a) tags
        anchorlinenos=True,
        # Wraps each line in a span tag with id='codeline-{line_number}'
        linespans='codeline',
    )

    formatter_other = DiffFormater(
        diff,
        False,
        # Adds line numbers column to output
        linenos='inline',
        # Wraps line numbers in link (a) tags
        anchorlinenos=True,
        # Wraps each line in a span tag with id='codeline-{line_number}'
        linespans='codeline',
    )

    return pygments.highlight(code, lexer, formatter), pygments.highlight(code_other, lexer, formatter_other)

