import re
import enum
from collections import namedtuple

# Supported token types
class TokenType(enum.Enum):
    WHITESPACE = 'whitespace',
    COMMENT = 'comment'
    STRING = 'string'
    NUMBER = 'number'
    IDENTIFIER = 'identifier'
    # may require extra parsing or context information
    SPECIAL = 'special'
    PUNCTUATION = 'punctuation'
    # lexing failure - should be logged, at least until update jobs are preemptible
    ERROR = 'error'

Token = namedtuple('Token', 'token_type, token, span, line')

def match_regex(regex):
    rule = re.compile(regex, flags=re.MULTILINE)
    return lambda code, pos, _: rule.match(code, pos)

def split_by_groups(*token_types):
    def split(ctx, match):
        pos = ctx.pos
        line = ctx.line
        for gi in range(len(match.groups())):
            token = match.group(gi+1)
            if len(token) != 0:
                action = token_types[gi]
                yield Token(action, token, (pos, pos+len(token)), line)
                line += token.count("\n")
                pos += len(token)

    return split

def token_from_match(ctx, match, token_type):
    span = match.span()
    result = Token(token_type, ctx.code[span[0]:span[1]], span, ctx.line)
    ctx.pos = span[1]
    ctx.line = ctx.line+result.token.count('\n')
    return result, ctx

def token_from_string(ctx, match, token_type):
    span = (ctx.pos, ctx.pos+len(match))
    result = Token(token_type, ctx.code[span[0]:span[1]], span, ctx.line)
    ctx.pos = span[1]
    ctx.line = ctx.line+result.token.count('\n')
    return result, ctx

# Interface class that allows to match only if certian conditions,
# hard to express in regex, are true
class Matcher:
    def update_after_match(self, code: str, pos: int, line: int, token: Token) -> None:
        pass

    def match(self, code: str, pos: int, line: int) -> None | re.Match:
        pass

# Match token only if it's the first token in line (skipping whitespace)
class FirstInLine(Matcher):
    whitespace = re.compile(r'\s*')

    def __init__(self, regex):
        self.rule = re.compile(regex, flags=re.MULTILINE)
        self.first_in_line = True

    def update_after_match(self, code, pos, line, token):
        # first token is always first in line
        if pos == 0:
            self.first_in_line = True
            return

        # check if matched token contains a newline
        newline_pos = code.rfind('\n', token.span[0], token.span[1])

        # if it doesn't contain a newline, check the part after newline
        if newline_pos != -1:
            post_newline_tok = code[newline_pos+1:token.span[1]]

            # if part after newline contains only whitespace (or nothing), the next token is first in line
            if self.whitespace.fullmatch(post_newline_tok):
                self.first_in_line = True
        # if currently matched is the first in line, and only contains whitespace,
        # the next token also counts as first in line
        elif self.first_in_line and self.whitespace.fullmatch(code, token.span[0], token.span[1]):
            self.first_in_line = True
        # otherwise reset first in line marker
        else:
            self.first_in_line = False

    def match(self, code, pos, line):
        if self.first_in_line:
            return self.rule.match(code, pos)

class LexerContext:
    def __init__(self, code, pos, line, filter_tokens):
        self.code = code
        self.pos = pos
        self.line = line
        self.filter_tokens = filter_tokens

def simple_lexer(rules, code, filter_tokens=None):
    if len(code) == 0:
        return

    # to avoid dealing with files without trailing newlines
    if code[-1] != '\n':
        code += '\n'

    rules_compiled = []
    after_match_hooks = []

    # compile rules
    for rule, action in rules:
        # string rules are actually match regex rules
        if type(rule) is str:
            rules_compiled.append((match_regex(rule), action))
        # rules can also be callables
        elif callable(rule):
            rules_compiled.append((rule, action))
        # rules can also be matchers - matchers get more information during parsing,
        # that information can stored in their state
        elif isinstance(rule, Matcher):
            rules_compiled.append((rule.match, action))
            after_match_hooks.append(rule.update_after_match)

    # helper function that calls hooks before yielding
    def yield_token(to_yield):
        for hook in after_match_hooks:
            hook(code, pos, line, to_yield)
        return to_yield

    pos = 0
    line = 1
    while pos < len(code):
        rule_matched = False
        for rule, action in rules_compiled:
            match = rule(code, pos, line)

            if match is not None:
                span = match.span()
                # if match is empty - continue
                if span[0] == span[1]:
                    continue

                rule_matched = True

                if isinstance(action, TokenType):
                    # only parse tokens of interest - slices apparently copy
                    if filter_tokens is None or action in filter_tokens:
                        token = code[span[0]:span[1]]
                    else:
                        token = None

                    token_obj = Token(action, token, span, line)
                    yield yield_token(token_obj)
                    line += code.count('\n', span[0], span[1])
                    pos = span[1]
                    break
                elif callable(action):
                    last_token = None
                    for token in action(LexerContext(code, pos, line, filter_tokens), match):
                        last_token = token
                        yield yield_token(token)

                    if last_token is not None:
                        pos = last_token.span[1]
                        line = last_token.line + last_token.token.count('\n')

                    break
                else:
                    raise Exception(f"invalid action {action}")

        # if no rules match, an error token with a single character is produced.
        # this isn't always a big problem, hence it's the decision of the caller
        # to decide whether to quit or continue
        if not rule_matched:
            token = Token(TokenType.ERROR, code[pos], (pos, pos+1), line)
            yield yield_token(token)
            if code[pos] == '\n':
                line += 1
            pos += 1

# Combines regexes passed as arguments with pipe operator
def regex_or(*regexes):
    result = '('
    for r in regexes:
        result += f'({ r })|'
    return result[:-1] + ')'

# Concatenates regexes, putting each in a separate group
def regex_concat(*regexes):
    result = ''
    for r in regexes:
        result += f'({ r })'
    return result

