import re
import os
from dataclasses import dataclass
from typing import Callable, List
from query import Query

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
    path: str
    get_ident_url: str
    get_absolute_source_url: Callable[[str], str]
    get_relative_source_url: Callable[[str], str]

# Filter interface/base class
# path_exceptions: list of regexes, disables filter if path of the filtered file matches a regex from the list
class Filter:
    def __init__(self, path_exceptions: List[str] = []):
        self.path_exceptions = path_exceptions

    # Return True if filter can be applied to file with path
    def check_if_applies(self, ctx: FilterContext) -> bool:
        for p in self.path_exceptions:
            if re.match(p, ctx.path):
                return False

        return True

    # Add information required by filter by transforming raw source code.
    # Known identifiers are marked by '\033[31m' and '\033[0m'
    def transform_raw_code(self, ctx: FilterContext, code: str) -> str:
        return code

    # Replace information left by `transform_raw_code` with target HTML
    # html: HTML output from code formatter
    def untransform_formatted_code(self, ctx: FilterContext, html: str) -> str:
        return html


# Returns true if filename from path (wihtout extension) is in the filenames iterable
def filename_without_ext_matches(path: str, filenames) -> bool:
    full_filename = os.path.basename(path)
    filename, _ = os.path.splitext(full_filename)
    return filename in filenames

# Returns true if extension of filename from path is in the extensions iterable
def extension_matches(path: str, extensions) -> bool:
    _, extension = os.path.splitext(path)
    extension = extension[1:].lower()
    return extension in extensions


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

