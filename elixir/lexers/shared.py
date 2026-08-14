from .utils import regex_or, regex_concat

# Regexes shared between lexers

whitespace = r'\s+'

# Building block for comments that start with a character and go until the end of the line
singleline_comment_with_escapes_base = r'(\\\s*\n|[^\n])*\n'

slash_star_multline_comment = r'/\*(.|\s)*?\*/'
double_slash_singleline_comment = r'//' + singleline_comment_with_escapes_base
common_slash_comment = regex_or(slash_star_multline_comment, double_slash_singleline_comment)

common_decimal_integer = r'[0-9][0-9\']*'
common_hexidecimal_integer = r'0[xX][0-9a-fA-F][0-9a-fA-F\']*'
common_octal_integer = r'0[0-7][0-7\']*'
common_binary_integer = r'0[bB][01][01\']*'

c_preproc_include = r'#\s*include\s*(<.*?>|".*?")'
# match warning and error directives with the error string
c_preproc_warning_and_error = r'#\s*(warning|error)\s(\\\s*\n|[^\n])*\n'
# match other preprocessor directives, but don't consume the whole line
c_preproc_other = r'#\s*[a-z]+'
c_preproc_ignore = regex_or(c_preproc_include, c_preproc_warning_and_error, c_preproc_other)

# \, any amount of whitespace, newline or any character that's not backslash newline or a quote, any escaped character
double_quote_string_with_escapes = r'"(\\\s*\n|[^\\"\n]|\\(.|\s))*?"'
single_quote_string_with_escapes = r"'(\\\s*\n|[^\\'\n]|\\(.|\s))*?'"

common_string_and_char = regex_or(double_quote_string_with_escapes, single_quote_string_with_escapes)

c_exponent = r'([eE][+-]?[0-9][0-9\']*)'
c_hexidecimal_exponent = r'([pP][+-]?[0-9][0-9\']*)'

c_decimal_double_part = r'\.[0-9\']*' + c_exponent + '?'
c_octal_double_part = r'\.[0-7\']*' + c_exponent + '?'
c_hexidecimal_double_part = r'\.[0-9a-fA-F\']*' + c_hexidecimal_exponent  + '?'

c_decimal = f'{ common_decimal_integer }({ c_decimal_double_part })?'
c_hexidecimal = f'{ common_hexidecimal_integer }({ c_hexidecimal_double_part })?'
c_octal = f'{ common_octal_integer }({ c_octal_double_part  })?'

# not entirely correct... accepts way more than the standard allows
c_number_suffix = r'([uU]|[lL]|(wb|WB)|[fF]|[zZ]){0,5}'

c_number = regex_concat(regex_or(c_hexidecimal, common_binary_integer, c_decimal, c_octal), c_number_suffix)

