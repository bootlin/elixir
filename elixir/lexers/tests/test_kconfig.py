from ..lexers import KconfigLexer
from .base import LexerTest

class KconfigLexerTest(LexerTest):
    lexer_cls = KconfigLexer
    default_filtered_tokens = ("SPECIAL", "COMMENT", "STRING", "IDENTIFIER", "SPECIAL", "ERROR")

    # TODO improve macro calls

    def test_comments(self):
        self.lex(r"""
# comment1
config 64BIT # comment2
    bool # comment3
    default "# asd"
    default $(shell, \#)
    help
        asdasdsajdlakjd # not a comment

        asdasdsajdlakjd # not a comment

        # comment 5

    # comment 6
""", [
            ['COMMENT', '# comment1\n'],
            ['SPECIAL', 'config'],
            ['IDENTIFIER', '64BIT'],
            ['COMMENT', '# comment2\n'],
            ['SPECIAL', 'bool'],
            ['COMMENT', '# comment3\n'],
            ['SPECIAL', 'default'],
            ['STRING', '"# asd"'],
            ['SPECIAL', 'default'],
            ['SPECIAL', 'shell'],
            ['SPECIAL', '\\#)'],
            ['SPECIAL', 'help'],
            ['COMMENT', '        asdasdsajdlakjd # not a comment\n\n        asdasdsajdlakjd # not a comment\n\n        # comment 5\n\n'],
            ['COMMENT', '# comment 6\n'],
        ])


    def test_keywords(self):
        self.lex(r""",
menu "menu name"

visible if y

choice
    prompt "test prompt"
    default y

config 86CONIFG
    bool "text"
    prompt "prompt"
    default y
    tristate "test"
    def_bool TEST_bool
    depends on TEST
    select TEST2
    imply TEST3
    range 5 512 if CONFIG_512
    help
        help text

        more help text

endmenu
""", [
        ['SPECIAL', 'menu'],
        ['STRING', '"menu name"'],
        ['SPECIAL', 'visible'],
        ['SPECIAL', 'if'],
        ['SPECIAL', 'y'],
        ['SPECIAL', 'choice'],
        ['SPECIAL', 'prompt'],
        ['STRING', '"test prompt"'],
        ['SPECIAL', 'default'],
        ['SPECIAL', 'y'],
        ['SPECIAL', 'config'],
        ['IDENTIFIER', '86CONIFG'],
        ['SPECIAL', 'bool'],
        ['STRING', '"text"'],
        ['SPECIAL', 'prompt'],
        ['STRING', '"prompt"'],
        ['SPECIAL', 'default'],
        ['SPECIAL', 'y'],
        ['SPECIAL', 'tristate'],
        ['STRING', '"test"'],
        ['SPECIAL', 'def_bool'],
        ['IDENTIFIER', 'TEST_bool'],
        ['SPECIAL', 'depends'],
        ['SPECIAL', 'on'],
        ['IDENTIFIER', 'TEST'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST2'],
        ['SPECIAL', 'imply'],
        ['IDENTIFIER', 'TEST3'],
        ['SPECIAL', 'range'],
        ['SPECIAL', 'if'],
        ['IDENTIFIER', 'CONFIG_512'],
        ['SPECIAL', 'help'],
        ['COMMENT', '        help text\n\n        more help text\n\n'],
        ['SPECIAL', 'endmenu'],
    ])

    def test_conditions(self):
        self.lex(r"""
config TEST
    select TEST1 if TEST2 = TEST3
    select TEST2 if TEST5 != TEST6
    select TEST7 if TEST8 < TEST9
    select TEST10 if TEST11 > TEST12
    select TEST13 if TEST14 <=  TEST15
""", [
        ['SPECIAL', 'config'],
        ['IDENTIFIER', 'TEST'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST1'],
        ['SPECIAL', 'if'],
        ['IDENTIFIER', 'TEST2'],
        ['PUNCTUATION', '='],
        ['IDENTIFIER', 'TEST3'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST2'],
        ['SPECIAL', 'if'],
        ['IDENTIFIER', 'TEST5'],
        ['PUNCTUATION', '!'],
        ['PUNCTUATION', '='],
        ['IDENTIFIER', 'TEST6'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST7'],
        ['SPECIAL', 'if'],
        ['IDENTIFIER', 'TEST8'],
        ['PUNCTUATION', '<'],
        ['IDENTIFIER', 'TEST9'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST10'],
        ['SPECIAL', 'if'],
        ['IDENTIFIER', 'TEST11'],
        ['PUNCTUATION', '>'],
        ['IDENTIFIER', 'TEST12'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST13'],
        ['SPECIAL', 'if'],
        ['IDENTIFIER', 'TEST14'],
        ['PUNCTUATION', '<'],
        ['PUNCTUATION', '='],
        ['IDENTIFIER', 'TEST15'],
    ], self.default_filtered_tokens + ("PUNCTUATION",))

    def test_conditions2(self):
        self.lex(r"""
config TEST
    select TEST16    if TEST17   >= TEST3
    select TEST17 if (TEST18 = TEST19)

    select TEST20 if !(TEST21 = TEST22)
    select TEST23 if TEST24 && TEST25
    select TEST26 if TEST27 || TEST28
""", [
        ['SPECIAL', 'config'],
        ['IDENTIFIER', 'TEST'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST16'],
        ['SPECIAL', 'if'],
        ['IDENTIFIER', 'TEST17'],
        ['PUNCTUATION', '>'],
        ['PUNCTUATION', '='],
        ['IDENTIFIER', 'TEST3'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST17'],
        ['SPECIAL', 'if'],
        ['PUNCTUATION', '('],
        ['IDENTIFIER', 'TEST18'],
        ['PUNCTUATION', '='],
        ['IDENTIFIER', 'TEST19'],
        ['PUNCTUATION', ')'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST20'],
        ['SPECIAL', 'if'],
        ['PUNCTUATION', '!'],
        ['PUNCTUATION', '('],
        ['IDENTIFIER', 'TEST21'],
        ['PUNCTUATION', '='],
        ['IDENTIFIER', 'TEST22'],
        ['PUNCTUATION', ')'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST23'],
        ['SPECIAL', 'if'],
        ['IDENTIFIER', 'TEST24'],
        ['PUNCTUATION', '&'],
        ['PUNCTUATION', '&'],
        ['IDENTIFIER', 'TEST25'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST26'],
        ['SPECIAL', 'if'],
        ['IDENTIFIER', 'TEST27'],
        ['PUNCTUATION', '|'],
        ['PUNCTUATION', '|'],
        ['IDENTIFIER', 'TEST28'],
    ], self.default_filtered_tokens + ("PUNCTUATION",))

    def test_macros(self):
        self.lex(r"""
config TEST
    depends on $(shell,cat file | grep -vi "option 2")
    depends on $(info,info to print)
    depends on $(warning-if,a != b,warning to print)
""", [
        ['SPECIAL', 'config'],
        ['IDENTIFIER', 'TEST'],
        ['SPECIAL', 'depends'],
        ['SPECIAL', 'on'],
        ['PUNCTUATION', '$'],
        ['PUNCTUATION', '('],
        ['SPECIAL', 'shell'],
        ['PUNCTUATION', ','],
        ['SPECIAL', 'cat'],
        ['SPECIAL', 'file'],
        ['PUNCTUATION', '|'],
        ['SPECIAL', 'grep'],
        ['PUNCTUATION', '-'],
        ['SPECIAL', 'vi'],
        ['STRING', '"option 2"'],
        ['PUNCTUATION', ')'],
        ['SPECIAL', 'depends'],
        ['SPECIAL', 'on'],
        ['PUNCTUATION', '$'],
        ['PUNCTUATION', '('],
        ['SPECIAL', 'info'],
        ['PUNCTUATION', ','],
        ['SPECIAL', 'info'],
        ['SPECIAL', 'to'],
        ['SPECIAL', 'print'],
        ['PUNCTUATION', ')'],
        ['SPECIAL', 'depends'],
        ['SPECIAL', 'on'],
        ['PUNCTUATION', '$'],
        ['PUNCTUATION', '('],
        ['SPECIAL', 'warning-if'],
        ['PUNCTUATION', ','],
        ['SPECIAL', 'a'],
        ['PUNCTUATION', '!'],
        ['PUNCTUATION', '='],
        ['SPECIAL', 'b'],
        ['PUNCTUATION', ','],
        ['SPECIAL', 'warning'],
        ['SPECIAL', 'to'],
        ['SPECIAL', 'print'],
        ['PUNCTUATION', ')'],
    ], self.default_filtered_tokens + ("PUNCTUATION",))

def test_macros2(self):
    self.lex(r"""
config TEST
    depends on $(error-if,a != b,warning to print)
    depends on $(filename)
    depends on $(lineno)
""", [
        ['SPECIAL', 'config'],
        ['IDENTIFIER', 'TEST'],
        ['SPECIAL', 'depends'],
        ['SPECIAL', 'on'],
        ['PUNCTUATION', '$'],
        ['PUNCTUATION', '('],
        ['SPECIAL', 'error-if'],
        ['PUNCTUATION', ','],
        ['SPECIAL', 'a'],
        ['PUNCTUATION', '!'],
        ['PUNCTUATION', '='],
        ['SPECIAL', 'b'],
        ['PUNCTUATION', ','],
        ['SPECIAL', 'warning'],
        ['SPECIAL', 'to'],
        ['SPECIAL', 'print'],
        ['PUNCTUATION', ')'],
        ['SPECIAL', 'depends'],
        ['SPECIAL', 'on'],
        ['PUNCTUATION', '$'],
        ['PUNCTUATION', '('],
        ['SPECIAL', 'filename'],
        ['PUNCTUATION', ')'],
        ['SPECIAL', 'depends'],
        ['SPECIAL', 'on'],
        ['PUNCTUATION', '$'],
        ['PUNCTUATION', '('],
        ['SPECIAL', 'lineno'],
        ['PUNCTUATION', ')'],
    ], self.default_filtered_tokens + ("PUNCTUATION",))

    def test_help(self):
        self.lex(r"""
config
    help
     help test lasdlkajdk sadlksajd
     lsajdlad

     salkdjaldlksajd

     "
     asdlkajsdlkjsadlajdsk

     salkdjlsakdj'
config
    select TEST
config
    ---help---
     help test lasdlkajdk sadlksajd
     lsajdlad

     salkdjaldlksajd
        
config
    select TEST
""", [
        ['SPECIAL', 'config'],
        ['SPECIAL', 'help'],
        ['COMMENT', '     help test lasdlkajdk sadlksajd\n     lsajdlad\n\n     salkdjaldlksajd\n\n     "\n     asdlkajsdlkjsadlajdsk\n\n     salkdjlsakdj\'\n'],
        ['SPECIAL', 'config'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST'],
        ['SPECIAL', 'config'],
        ['SPECIAL', '---help---'],
        ['COMMENT', '     help test lasdlkajdk sadlksajd\n     lsajdlad\n\n     salkdjaldlksajd\n        \n'],
        ['SPECIAL', 'config'],
        ['SPECIAL', 'select'],
        ['IDENTIFIER', 'TEST'],
    ])

    def test_types(self):
        self.lex(r"""
config
    bool
    default y

config
    tristate
    default m

config
    hex
	default 0xdfffffff00000000

config
    string
    default "string \" test # \# zxc"

config
    int
    default 21312323
""", [
        ['SPECIAL', 'config'],
        ['SPECIAL', 'bool'],
        ['SPECIAL', 'default'],
        ['SPECIAL', 'y'],
        ['SPECIAL', 'config'],
        ['SPECIAL', 'tristate'],
        ['SPECIAL', 'default'],
        ['SPECIAL', 'm'],
        ['SPECIAL', 'config'],
        ['SPECIAL', 'hex'],
        ['SPECIAL', 'default'],
        ['IDENTIFIER', '0xdfffffff00000000'],
        ['SPECIAL', 'config'],
        ['SPECIAL', 'string'],
        ['SPECIAL', 'default'],
        ['STRING', '"string \\" test # \\# zxc"'],
        ['SPECIAL', 'config'],
        ['SPECIAL', 'int'],
        ['SPECIAL', 'default'],
    ])
