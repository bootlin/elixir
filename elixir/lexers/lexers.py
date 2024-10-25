import re

from . import shared
from .utils import TokenType, simple_lexer, FirstInLine, split_by_groups, regex_concat, token_from_string

# Lexers used to extract possible references from source files
# Design inspired by Pygments lexers interface

# https://en.cppreference.com/w/c/language
# https://www.iso-9899.info/wiki/The_Standard
class CLexer:
    # NOTE: does not support unicode identifiers
    c_identifier = r'[a-zA-Z_][a-zA-Z_0-9]*'

    c_punctuation = r'[!#%&`()*+,./:;<=>?\[\]\\^_{|}~-]'

    # NOTE: macros don't always contain C code, but detecting that in pratice is hard
    # without information about context (where the file is included from).
    c_punctuation_extra = r'[$\\@]'

    rules = [
        (shared.whitespace, TokenType.WHITESPACE),
        (shared.common_slash_comment, TokenType.COMMENT),
        (shared.common_string_and_char, TokenType.STRING),
        (shared.c_number, TokenType.NUMBER),
        (c_identifier, TokenType.IDENTIFIER),
        (FirstInLine(shared.c_preproc_ignore), TokenType.SPECIAL),
        (c_punctuation, TokenType.PUNCTUATION),
        (c_punctuation_extra, TokenType.PUNCTUATION),
    ]

    def __init__(self, code):
        self.code = code

    def lex(self, **kwargs):
        return simple_lexer(self.rules, self.code, **kwargs)


# https://www.devicetree.org/specifications/
class DTSLexer:
    # TODO handle macros separately

    # NOTE: previous versions would split identifiers by commas (and other special characters),
    # this changes the old behavior

    # 6.2
    # technically shall be 1-31 characters long BUT /linux/v6.9.4/source/arch/arm64/boot/dts/qcom/sm8250.dtsi#L3506
    dts_label = r'[a-zA-Z_][a-zA-Z_0-9]*'
    # no whitespace between label and ampersand/colon is allowed
    dts_label_reference = f'(&)({ dts_label })'
    dts_label_definition = f'({ dts_label })(:)'

    # 2.2.1
    # same with label lenght, just in case
    dts_node_name = r'[a-zA-Z0-9,._+-]+'
    # can contain macro symbols
    dts_unit_address = r'[a-zA-Z0-9,._+-]*'

    dts_node_name_with_unit_address = f'({ dts_node_name })(@)({ dts_unit_address })' + r'(\s*)({)'
    dts_node_name_without_unit_address = f'({ dts_node_name })' + r'(\s*)({)'

    # 2.2.4
    dts_property_name = r'[0-9a-zA-Z,._+?#-]+'
    dts_property_assignment = f'({ dts_property_name })' + r'(\s*)(=)'
    dts_property_empty = f'({ dts_property_name })' + r'(\s*)(;)'

    dts_directive = r'/[a-zA-Z0-9-]+/';
    dts_delete_node = regex_concat(r'/delete-node/\s+', dts_node_name)
    dts_delete_property = regex_concat(r'/delete-property/\s+', dts_property_name)

    # 6.3
    dts_node_reference = r'(&)({)([a-zA-Z0-9,._+/@-]+?)(})'

    dts_punctuation = r'[#@:;{}\[\]()^<>=+*/%&\\|~!?,-]'
    # other, unknown, identifiers - for exmple macros
    dts_default_identifier = r'[0-9a-zA-Z_]+'

    # Parse DTS node reference, ex: &{/path/to/node@20/test}
    @staticmethod
    def parse_dts_node_reference(ctx, match):
        # &
        token, ctx = token_from_string(ctx, match.group(1), TokenType.PUNCTUATION)
        yield token

        # {
        token, ctx = token_from_string(ctx, match.group(2), TokenType.PUNCTUATION)
        yield token

        path = match.group(3)
        path_part_matcher = re.compile(DTSLexer.dts_unit_address)
        strpos = 0

        while strpos < len(path):
            if path[strpos] == '@' or path[strpos] == '/':
                token, ctx = token_from_string(ctx, path[strpos], TokenType.PUNCTUATION)
                yield token
                strpos += 1
            else:
                part_match = path_part_matcher.match(path, strpos)
                if part_match is None:
                    token, _ = token_from_string(ctx, TokenType.ERROR, '')
                    yield token
                    return None

                token, ctx = token_from_string(ctx, part_match.group(0), TokenType.IDENTIFIER)
                yield token
                strpos += len(part_match.group(0))
        # }
        token, ctx = token_from_string(ctx, match.group(4), TokenType.PUNCTUATION)
        yield token

    rules = [
        (shared.whitespace, TokenType.WHITESPACE),
        (shared.common_slash_comment, TokenType.COMMENT),
        (shared.common_string_and_char, TokenType.STRING),
        (shared.c_number, TokenType.NUMBER),

        (dts_label_reference, split_by_groups(TokenType.PUNCTUATION, TokenType.IDENTIFIER)),
        (dts_label_definition, split_by_groups(TokenType.IDENTIFIER, TokenType.PUNCTUATION)),
        (dts_node_reference, parse_dts_node_reference),

        (dts_property_assignment,
         split_by_groups(TokenType.IDENTIFIER, TokenType.WHITESPACE, TokenType.PUNCTUATION)),
        (dts_property_empty,
         split_by_groups(TokenType.IDENTIFIER, TokenType.WHITESPACE, TokenType.PUNCTUATION)),

        (dts_node_name_with_unit_address,
         split_by_groups(TokenType.IDENTIFIER, TokenType.PUNCTUATION,
                    TokenType.IDENTIFIER, TokenType.WHITESPACE, TokenType.PUNCTUATION)),
        (dts_node_name_without_unit_address,
         split_by_groups(TokenType.IDENTIFIER, TokenType.WHITESPACE, TokenType.PUNCTUATION)),

        (dts_directive, TokenType.SPECIAL),
        (dts_delete_node, split_by_groups(TokenType.SPECIAL, TokenType.IDENTIFIER)),
        (dts_delete_property, split_by_groups(TokenType.SPECIAL, TokenType.IDENTIFIER)),
        (dts_default_identifier, TokenType.IDENTIFIER),
        (FirstInLine(shared.c_preproc_ignore), TokenType.SPECIAL),
        (dts_punctuation, TokenType.PUNCTUATION),
    ]

    def __init__(self, code):
        self.code = code

    def lex(self, **kwargs):
        return simple_lexer(self.rules, self.code, **kwargs)

