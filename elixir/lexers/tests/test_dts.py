from ..lexers import DTSLexer
from .base import LexerTest

class DTSLexerTests(LexerTest):
    lexer_cls = DTSLexer
    default_filtered_tokens = ("SPECIAL", "COMMENT", "STRING", "IDENTIFIER", "SPECIAL", "ERROR")

    def test_preproc(self):
        self.lex(r"""
#include <file.dtsi>
#include "file2.dtsi"
#error error message asldjlksajdlksad
#warning   warning message alsjdlkasjdlksajd
#define MACRO(arg) \
        arg = <3>;
#if 0
/ {
    property = <2>;
    MACRO(test)
};
#endif
""", [
        ['SPECIAL', '#include <file.dtsi>'],
        ['SPECIAL', '#include "file2.dtsi"'],
        ['SPECIAL', '#error error message asldjlksajdlksad\n'],
        ['SPECIAL', '#warning   warning message alsjdlkasjdlksajd\n'],
        ['SPECIAL', '#define'],
        ['IDENTIFIER', 'MACRO'],
        ['IDENTIFIER', 'arg'],
        ['IDENTIFIER', 'arg'],
        ['SPECIAL', '#if'],
        ['IDENTIFIER', 'property'],
        ['IDENTIFIER', 'MACRO'],
        ['IDENTIFIER', 'test'],
        ['SPECIAL', '#endif'],
    ])

    def test_dts_directives(self):
        self.lex(r"""
/include/ "file.dtsi"
/dts-v1/;
/memreserve/ 0x100 0x2;
/ {
    test_label: test-node {
        test-prop2 = <3>;
    };
    test-prop = <2>;
    /delete-node/ test-node;
    /delete-node/ &test_label;
    /delete-property/ test-prop;
};
""", [
        ['SPECIAL', '/include/'],
        ['STRING', '"file.dtsi"'],
        ['SPECIAL', '/dts-v1/'],
        ['SPECIAL', '/memreserve/'],
        ['IDENTIFIER', 'test_label'],
        ['IDENTIFIER', 'test-node'],
        ['IDENTIFIER', 'test-prop2'],
        ['IDENTIFIER', 'test-prop'],
        ['SPECIAL', '/delete-node/'],
        ['IDENTIFIER', 'test-node'],
        ['SPECIAL', '/delete-node/'],
        ['IDENTIFIER', 'test_label'],
        ['SPECIAL', '/delete-property/'],
        ['IDENTIFIER', 'test-prop'],
    ])

    def test_dts_unusual_identifiers(self):
        self.lex(r"""
/ {
    _test_label:        5id,test._+asd-2           {
        property,name = <2>;
        0p,r.o_p+e?r#t-y,name = [1,2,3];
        way_too_long_label_123219380921830218309218309213    :  node@234 {
            compatible = "asd,zxc";
        }
        test  =   <&way_too_long_label_123219380921830218309218309213>;
    };
};
""", [
        ['IDENTIFIER', '_test_label'],
        ['IDENTIFIER', 'id,test._+asd-2'],
        ['IDENTIFIER', 'property,name'],
        ['IDENTIFIER', 'p,r.o_p+e?r#t-y,name'],
        ['IDENTIFIER', 'way_too_long_label_123219380921830218309218309213'],
        ['IDENTIFIER', 'node'],
        ['IDENTIFIER', '234'],
        ['IDENTIFIER', 'compatible'],
        ['STRING', '"asd,zxc"'],
        ['IDENTIFIER', 'test'],
        ['IDENTIFIER', 'way_too_long_label_123219380921830218309218309213'],
    ])

    def test_non_numeric_unit_address(self):
        self.lex(r"""
/ {
    test: node@test_address {
    };
    test2: node@MACRO_ADDRESS(123) {
    };
};
""", [
        ['IDENTIFIER', 'test'],
        ['IDENTIFIER', 'node'],
        ['IDENTIFIER', 'test_address'],
        ['IDENTIFIER', 'test2'],
        ['IDENTIFIER', 'node'],
        ['IDENTIFIER', 'MACRO_ADDRESS'],
    ])

    def test_values_with_labels(self):
        self.lex(r"""
/ {
    prop1 = label1: <0 label2: 0x21323>;
    prop2 = [1 2 3 label3: 4];
    prop3 = label4: "val" label5: ;
};
""", [
        ['PUNCTUATION', '/'],
        ['PUNCTUATION', '{'],
        ['IDENTIFIER', 'prop1'],
        ['PUNCTUATION', '='],
        ['IDENTIFIER', 'label1'],
        ['PUNCTUATION', ':'],
        ['PUNCTUATION', '<'],
        ['NUMBER', '0'],
        ['IDENTIFIER', 'label2'],
        ['PUNCTUATION', ':'],
        ['NUMBER', '0x21323'],
        ['PUNCTUATION', '>'],
        ['PUNCTUATION', ';'],
        ['IDENTIFIER', 'prop2'],
        ['PUNCTUATION', '='],
        ['PUNCTUATION', '['],
        ['NUMBER', '1'],
        ['NUMBER', '2'],
        ['NUMBER', '3'],
        ['IDENTIFIER', 'label3'],
        ['PUNCTUATION', ':'],
        ['NUMBER', '4'],
        ['PUNCTUATION', ']'],
        ['PUNCTUATION', ';'],
        ['IDENTIFIER', 'prop3'],
        ['PUNCTUATION', '='],
        ['IDENTIFIER', 'label4'],
        ['PUNCTUATION', ':'],
        ['STRING', '"val"'],
        ['IDENTIFIER', 'label5'],
        ['PUNCTUATION', ':'],
        ['PUNCTUATION', ';'],
        ['PUNCTUATION', '}'],
        ['PUNCTUATION', ';'],
    ], self.default_filtered_tokens + ('PUNCTUATION', 'NUMBER'))

    def test_references(self):
        self.lex(r"""
/ {
    interrupt-parent = < &{/node@c2342/another_node@address(2)/node3} >;
    property2 = <&{/node@c2342/another_node@address(2)}>;
    power-domains = <&power DEVICE_DOMAIN>;
};
""", [
        ['IDENTIFIER', 'interrupt-parent'],
        ['IDENTIFIER', 'node'],
        ['IDENTIFIER', 'c2342'],
        ['IDENTIFIER', 'another_node'],
        ['IDENTIFIER', 'address'],
        ['IDENTIFIER', 'node3'],
        ['IDENTIFIER', 'property2'],
        ['IDENTIFIER', 'node'],
        ['IDENTIFIER', 'c2342'],
        ['IDENTIFIER', 'another_node'],
        ['IDENTIFIER', 'address'],
        ['IDENTIFIER', 'power-domains'],
        ['IDENTIFIER', 'power'],
        ['IDENTIFIER', 'DEVICE_DOMAIN'],
    ])

    def test_property_types(self):
        self.lex(r"""
/ {
    prop1 = <0 0x21323>;
    prop2 = [1 2 3 4];
    prop3 = "val", "val4" ;
    prop4 = <~1+2-3*4/5%6&7|8^9<<10>>11>;
    prop5;
};
""", [
        ['PUNCTUATION', '/'],
        ['PUNCTUATION', '{'],
        ['IDENTIFIER', 'prop1'],
        ['PUNCTUATION', '='],
        ['PUNCTUATION', '<'],
        ['NUMBER', '0'],
        ['NUMBER', '0x21323'],
        ['PUNCTUATION', '>'],
        ['PUNCTUATION', ';'],
        ['IDENTIFIER', 'prop2'],
        ['PUNCTUATION', '='],
        ['PUNCTUATION', '['],
        ['NUMBER', '1'],
        ['NUMBER', '2'],
        ['NUMBER', '3'],
        ['NUMBER', '4'],
        ['PUNCTUATION', ']'],
        ['PUNCTUATION', ';'],
        ['IDENTIFIER', 'prop3'],
        ['PUNCTUATION', '='],
        ['STRING', '"val"'],
        ['PUNCTUATION', ','],
        ['STRING', '"val4"'],
        ['PUNCTUATION', ';'],
        ['IDENTIFIER', 'prop4'],
        ['PUNCTUATION', '='],
        ['PUNCTUATION', '<'],
        ['PUNCTUATION', '~'],
        ['NUMBER', '1'],
        ['PUNCTUATION', '+'],
        ['NUMBER', '2'],
        ['PUNCTUATION', '-'],
        ['NUMBER', '3'],
        ['PUNCTUATION', '*'],
        ['NUMBER', '4'],
        ['PUNCTUATION', '/'],
        ['NUMBER', '5'],
        ['PUNCTUATION', '%'],
        ['NUMBER', '6'],
        ['PUNCTUATION', '&'],
        ['NUMBER', '7'],
        ['PUNCTUATION', '|'],
        ['NUMBER', '8'],
        ['PUNCTUATION', '^'],
        ['NUMBER', '9'],
        ['PUNCTUATION', '<'],
        ['PUNCTUATION', '<'],
        ['NUMBER', '10'],
        ['PUNCTUATION', '>'],
        ['PUNCTUATION', '>'],
        ['NUMBER', '11'],
        ['PUNCTUATION', '>'],
        ['PUNCTUATION', ';'],
        ['IDENTIFIER', 'prop5'],
        ['PUNCTUATION', ';'],
        ['PUNCTUATION', '}'],
        ['PUNCTUATION', ';'],
    ], self.default_filtered_tokens + ('PUNCTUATION', 'NUMBER'))

    def test_comments(self):
        self.lex(r"""
//license info
/ {
    interrupts = <NAME 100 TYPE>, /* comment 1 */
        <NAME 101 TYPE>; // comemnt2
    /* long
    * coment
    * asdasd
    */
};
""", [
        ['COMMENT', '//license info\n'],
        ['IDENTIFIER', 'interrupts'],
        ['IDENTIFIER', 'NAME'],
        ['IDENTIFIER', 'TYPE'],
        ['COMMENT', '/* comment 1 */'],
        ['IDENTIFIER', 'NAME'],
        ['IDENTIFIER', 'TYPE'],
        ['COMMENT', '// comemnt2\n'],
        ['COMMENT', '/* long\n    * coment\n    * asdasd\n    */'],
    ], self.default_filtered_tokens)

