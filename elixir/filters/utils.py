import re
import os
from dataclasses import dataclass
from typing import Callable, List
from ..query import Query

# Context data used by Filters
# tag: browsed version, unqoted
# family: family of file
# path: path of file
# get_ident_url: function that returns URL to identifier passed as argument
# get_absolute_source_url: function that returns a URL to file with absolute path passed as an argument
# get_relative_source_url: function that returns a URL to file in directory of current file
@dataclass
class FilterContext:
    query: Query
    tag: str
    family: str
    filepath: str
    get_ident_url: Callable[[str], str]
    get_absolute_source_url: Callable[[str], str]
    get_relative_source_url: Callable[[str], str]

# Filter interface/base class
# Filters are used to add extra information, like links, to code formatted into HTML by Pygments.
# Filters consist of two parts: the first part runs on unformatted code, transforming it
# to mark interesting identifiers, for example keywords. How the identifiers are marked is
# up to the filter, but it's important to be careful to not break formatting.
# The second part runs on HTML, replacing markings left by the first part with HTML code.
# path_exceptions: list of regexes, disables filter if path of the filtered file matches a regex from the list
class Filter:
    def __init__(self, path_exceptions: List[str] = []):
        self.path_exceptions = path_exceptions

    # Return True if filter can be applied to file with path
    def check_if_applies(self, ctx: FilterContext) -> bool:
        for p in self.path_exceptions:
            if re.match(p, ctx.filepath):
                return False

        return True

    # Add information required by filter by transforming raw source code.
    # Known identifiers are marked by '\033[31m' and '\033[0m'. Note that these marked
    # identifiers are usually handled by IdentFilter or KconfigIdentsFilter.
    def transform_raw_code(self, ctx: FilterContext, code: str) -> str:
        return code

    # Replace information left by `transform_raw_code` with target HTML
    # html: HTML output from code formatter
    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        return html


# Returns true if filename from filepath, with removed extension, is in the
# allowed_filenames_without_ext iterable
def filename_without_ext_matches(filepath: str, allowed_filenames_without_ext) -> bool:
    filename = os.path.basename(filepath)
    filename_without_ext, _ = os.path.splitext(filename)
    return filename_without_ext in allowed_filenames_without_ext

# Returns true if extension of filename from filepath is in the
# allowed_extensions iterable
def extension_matches(filepath: str, allowed_extensions) -> bool:
    _, file_ext_dot = os.path.splitext(filepath)
    file_ext = file_ext_dot[1:].lower()
    return file_ext in allowed_extensions


# Encodes an integer into a string of characters (A-J)
# encode_number(10239) = 'BACDJ'
def encode_number(number):
    result = ''

    while number != 0:
        number, rem = divmod(number, 10)
        rem = chr(ord('A') + rem)
        result = rem + result

    return result

# Decodes a string of characters returned by encode_number into an integer
# decode_number('BACDJ') = 10239
def decode_number(string):
    result = ''

    while string != '':
        string, char = string[:-1], string[-1]
        char = str(ord(char) - ord('A'))
        result = char + result

    return int(result)

def format_source_link(url: str, label: str) -> str:
    return f'<a class="source-link" href="{ url }">{ label }</a>'

