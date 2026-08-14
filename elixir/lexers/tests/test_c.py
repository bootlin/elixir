from ..lexers import CLexer
from .base import LexerTest

class CLexerTest(LexerTest):
    lexer_cls = CLexer
    default_filtered_tokens = ("SPECIAL", "COMMENT", "STRING", "IDENTIFIER", "SPECIAL", "ERROR")

    def test_if0(self):
        self.lex(r"""
#if 0
static bool test_v3_0_test(void *h,
                    enum type_enum e) {
    return false;
}
#endif
static bool test_v3_0_test(void *h,
                    enum type_enum e) {
    return false;
}
""", [
        ['SPECIAL', '#if'],
        ['NUMBER', '0'],
        ['IDENTIFIER', 'static'],
        ['IDENTIFIER', 'bool'],
        ['IDENTIFIER', 'test_v3_0_test'],
        ['IDENTIFIER', 'void'],
        ['IDENTIFIER', 'h'],
        ['IDENTIFIER', 'enum'],
        ['IDENTIFIER', 'type_enum'],
        ['IDENTIFIER', 'e'],
        ['IDENTIFIER', 'return'],
        ['IDENTIFIER', 'false'],
        ['SPECIAL', '#endif'],
        ['IDENTIFIER', 'static'],
        ['IDENTIFIER', 'bool'],
        ['IDENTIFIER', 'test_v3_0_test'],
        ['IDENTIFIER', 'void'],
        ['IDENTIFIER', 'h'],
        ['IDENTIFIER', 'enum'],
        ['IDENTIFIER', 'type_enum'],
        ['IDENTIFIER', 'e'],
        ['IDENTIFIER', 'return'],
        ['IDENTIFIER', 'false'],
    ], self.default_filtered_tokens + ("NUMBER",))

    def test_preproc(self):
        self.lex(r"""
#include <stdio.h>
#   include <stdio.h>
# include "test.h"
#   include "test.h"

# warning war
#       error err
    #       error err
    #warning war

#error "escaped\
        message"

#warning "escaped\  
        message"

#  if defined(TEST)
#   elif defined(TEST2)
#else
""", [
        ['SPECIAL', '#include <stdio.h>'],
        ['SPECIAL', '#   include <stdio.h>'],
        ['SPECIAL', '# include "test.h"'],
        ['SPECIAL', '#   include "test.h"'],
        ['SPECIAL', '# warning war\n'],
        ['SPECIAL', '#       error err\n'],
        ['SPECIAL', '#       error err\n'],
        ['SPECIAL', '#warning war\n'],
        ['SPECIAL', '#error "escaped\\\n        message"\n'],
        ['SPECIAL', '#warning "escaped\\  \n        message"\n'],
        ['SPECIAL', '#  if'],
        ['IDENTIFIER', 'defined'],
        ['IDENTIFIER', 'TEST'],
        ['SPECIAL', '#   elif'],
        ['IDENTIFIER', 'defined'],
        ['IDENTIFIER', 'TEST2'],
        ['SPECIAL', '#else'],
    ])

    def test_defines(self):
        self.lex("""
# define test "long string \
    escaped newline"

    #define     test define1
#       define     test2 define12323

#define func(name, arg1,arg2...) \
    void name##f() { \
        return arg1 + arg2;
    }
""", [
        ['SPECIAL', '# define'],
        ['IDENTIFIER', 'test'],
        ['STRING', '"long string     escaped newline"'],
        ['SPECIAL', '#define'],
        ['IDENTIFIER', 'test'],
        ['IDENTIFIER', 'define1'],
        ['SPECIAL', '#       define'],
        ['IDENTIFIER', 'test2'],
        ['IDENTIFIER', 'define12323'],
        ['SPECIAL', '#define'],
        ['IDENTIFIER', 'func'],
        ['IDENTIFIER', 'name'],
        ['IDENTIFIER', 'arg1'],
        ['IDENTIFIER', 'arg2'],
        ['IDENTIFIER', 'void'],
        ['IDENTIFIER', 'name'],
        ['IDENTIFIER', 'f'],
        ['IDENTIFIER', 'return'],
        ['IDENTIFIER', 'arg1'],
        ['IDENTIFIER', 'arg2'],
    ])

    def test_strings(self):
        self.lex(r"""
"asdsad \   
    asdasd";
'asdsad \
    asdasd';
u8"test string";
u"test string";
u"test string";
L"test string";
"test \" string";
"test ' string";
"test \' string";
"test \n string";
"\xff";
"test" "string";
"test""string";
"test"
""", [
        ['STRING', '"asdsad \\   \n    asdasd"'],
        ['STRING', "'asdsad \\\n    asdasd'"],
        ['IDENTIFIER', 'u8'],
        ['STRING', '"test string"'],
        ['IDENTIFIER', 'u'],
        ['STRING', '"test string"'],
        ['IDENTIFIER', 'u'],
        ['STRING', '"test string"'],
        ['IDENTIFIER', 'L'],
        ['STRING', '"test string"'],
        ['STRING', '"test \\" string"'],
        ['STRING', '"test \' string"'],
        ['STRING', '"test \\\' string"'],
        ['STRING', '"test \\n string"'],
        ['STRING', '"\\xff"'],
        ['STRING', '"test"'],
        ['STRING', '"string"'],
        ['STRING', '"test"'],
        ['STRING', '"string"'],
        ['STRING', '"test"'],
    ])

    def test_strings2(self):
        self.lex(r"""
    "string";
        char* s1 = "asdjlsajdlksad""asdsajdlsad";       //comment6
    char* s2 = "asdjlsajdlksad"  "asdsajdlsad";         // \
                                                        single line comment \
        with escapes
    char* s3 = " asdsaldjkas \"";
    char* s4 = " asdsaldjkas \" zxclzxclk \" asljda";
    char* s5 = " asdsaldjkas \' zxclzxclk \" asljda";
    char* s6 = " asdsaldjkas \"\"\" zxclzxclk \'\'\' ; asljda";
    char* s7 = u8"test";
""", [
        ['STRING', '"string"'],
        ['IDENTIFIER', 'char'],
        ['IDENTIFIER', 's1'],
        ['STRING', '"asdjlsajdlksad"'],
        ['STRING', '"asdsajdlsad"'],
        ['COMMENT', '//comment6\n'],
        ['IDENTIFIER', 'char'],
        ['IDENTIFIER', 's2'],
        ['STRING', '"asdjlsajdlksad"'],
        ['STRING', '"asdsajdlsad"'],
        ['COMMENT', '// \\\n                                                        single line comment \\\n        with escapes\n'],
        ['IDENTIFIER', 'char'],
        ['IDENTIFIER', 's3'],
        ['STRING', '" asdsaldjkas \\""'],
        ['IDENTIFIER', 'char'],
        ['IDENTIFIER', 's4'],
        ['STRING', '" asdsaldjkas \\" zxclzxclk \\" asljda"'],
        ['IDENTIFIER', 'char'],
        ['IDENTIFIER', 's5'],
        ['STRING', '" asdsaldjkas \\\' zxclzxclk \\" asljda"'],
        ['IDENTIFIER', 'char'],
        ['IDENTIFIER', 's6'],
        ['STRING', '" asdsaldjkas \\"\\"\\" zxclzxclk \\\'\\\'\\\' ; asljda"'],
        ['IDENTIFIER', 'char'],
        ['IDENTIFIER', 's7'],
        ['IDENTIFIER', 'u8'],
        ['STRING', '"test"'],
    ])

    def test_chars(self):
        self.lex(r"""
'a';
u8'a';
u'a';
U'a';
'\'';
'\"';
'\\';
'\n';
'\f';
'\U0001f34c';
'\13';
'\x1234';
'\u213';
u'ą';
""", [
        ['STRING', "'a'"],
        ['IDENTIFIER', 'u8'],
        ['STRING', "'a'"],
        ['IDENTIFIER', 'u'],
        ['STRING', "'a'"],
        ['IDENTIFIER', 'U'],
        ['STRING', "'a'"],
        ['STRING', "'\\''"],
        ['STRING', '\'\\"\''],
        ['STRING', "'\\\\'"],
        ['STRING', "'\\n'"],
        ['STRING', "'\\f'"],
        ['STRING', "'\\U0001f34c'"],
        ['STRING', "'\\13'"],
        ['STRING', "'\\x1234'"],
        ['STRING', "'\\u213'"],
        ['IDENTIFIER', 'u'],
        ['STRING', "'ą'"],
    ])

    def test_numbers(self):
        self.lex(r"""
1239183;
-1239183;
0xAB08902;
-0xAB08902;
0Xab08902;
-0Xab08902;
0b0101001;
-0b0101001;
0B0101001;
-0B0101001;
0231273;
-0231273;
""", [
        ['NUMBER', '1239183'],
        ['NUMBER', '1239183'],
        ['NUMBER', '0xAB08902'],
        ['NUMBER', '0xAB08902'],
        ['NUMBER', '0Xab08902'],
        ['NUMBER', '0Xab08902'],
        ['NUMBER', '0b0101001'],
        ['NUMBER', '0b0101001'],
        ['NUMBER', '0B0101001'],
        ['NUMBER', '0B0101001'],
        ['NUMBER', '0231273'],
        ['NUMBER', '0231273'],
    ], self.default_filtered_tokens + ("NUMBER",))

    def test_floats(self):
        self.lex(r"""
double       e = 0x2ABDEFabcdef;
double
    f = 017.048509495;
double     -g = 0b1010010;
double     g = 0b1010010;
-017.048509495;
017.048509495;
-017.048509495e-12329123;
017.048509495e-12329123;
-0x123.fp34;
0x123.fp34;
-0x123.fP34;
0x123.fP34;
-0x123.fe1p123;
0x123.fe1p123;
-0x123.fe1p123;
0x123.fe1p123;
-.1;
.1;
-1.;
1.;
-0x1.ep+3;
0x1.ep+3;
-0X183083;
0X183083;
-0x213213.1231212'31e21p-2;
0x213213.1231212'31e21p-2;
-123123.123e2;
123123.123e2;
""", [
        ['IDENTIFIER', 'double'],
        ['IDENTIFIER', 'e'],
        ['NUMBER', '0x2ABDEFabcdef'],
        ['IDENTIFIER', 'double'],
        ['IDENTIFIER', 'f'],
        ['NUMBER', '017.048509495'],
        ['IDENTIFIER', 'double'],
        ['IDENTIFIER', 'g'],
        ['NUMBER', '0b1010010'],
        ['IDENTIFIER', 'double'],
        ['IDENTIFIER', 'g'],
        ['NUMBER', '0b1010010'],
        ['NUMBER', '017.048509495'],
        ['NUMBER', '017.048509495'],
        ['NUMBER', '017.048509495e-12329123'],
        ['NUMBER', '017.048509495e-12329123'],
        ['NUMBER', '0x123.fp34'],
        ['NUMBER', '0x123.fp34'],
        ['NUMBER', '0x123.fP34'],
        ['NUMBER', '0x123.fP34'],
        ['NUMBER', '0x123.fe1p123'],
        ['NUMBER', '0x123.fe1p123'],
        ['NUMBER', '0x123.fe1p123'],
        ['NUMBER', '0x123.fe1p123'],
        ['NUMBER', '1'],
        ['NUMBER', '1'],
        ['NUMBER', '1.'],
        ['NUMBER', '1.'],
        ['NUMBER', '0x1.ep+3'],
        ['NUMBER', '0x1.ep+3'],
        ['NUMBER', '0X183083'],
        ['NUMBER', '0X183083'],
        ['NUMBER', "0x213213.1231212'31e21p-2"],
        ['NUMBER', "0x213213.1231212'31e21p-2"],
        ['NUMBER', '123123.123e2'],
        ['NUMBER', '123123.123e2'],
    ], self.default_filtered_tokens + ("NUMBER",))

    def test_longs(self):
        self.lex(r"""
-123213092183ul;
123213092183ul;
-123213092183ull;
123213092183ull;
-123213092183llu;
123213092183llu;
-123213092183uLL;
123213092183uLL;
-123213092183LLU;
123213092183LLU;
-1232'13092183LLU;
1232'13092183LLU;
-1232'1309'2183LLU;
1232'1309'2183LLU;
-1232'1309'218'3LLU;
1232'1309'218'3LLU;
""", [
        ['NUMBER', '123213092183ul'],
        ['NUMBER', '123213092183ul'],
        ['NUMBER', '123213092183ull'],
        ['NUMBER', '123213092183ull'],
        ['NUMBER', '123213092183llu'],
        ['NUMBER', '123213092183llu'],
        ['NUMBER', '123213092183uLL'],
        ['NUMBER', '123213092183uLL'],
        ['NUMBER', '123213092183LLU'],
        ['NUMBER', '123213092183LLU'],
        ['NUMBER', "1232'13092183LLU"],
        ['NUMBER', "1232'13092183LLU"],
        ['NUMBER', "1232'1309'2183LLU"],
        ['NUMBER', "1232'1309'2183LLU"],
        ['NUMBER', "1232'1309'218'3LLU"],
        ['NUMBER', "1232'1309'218'3LLU"],
    ], self.default_filtered_tokens + ("NUMBER",))

    def test_comments(self):
        self.lex(r"""
    /*comment1*/
    /* comment2*/
    /* comment3 */
    /*
     *
        comment4
    _+}{|":?><~!@#$%&*()_+`123567890-=[];'\,./
     * */

    /* comment 5 \*\// */

// comment5
char* s2 = "asdjlsajdlksad"  "asdsajdlsad";         // \
                                   single line comment \
        with escapes
char statement;
""", [
        ['COMMENT', '/*comment1*/'],
        ['COMMENT', '/* comment2*/'],
        ['COMMENT', '/* comment3 */'],
        ['COMMENT', '/*\n     *\n        comment4\n    _+}{|":?><~!@#$%&*()_+`123567890-=[];\'\\,./\n     * */'],
        ['COMMENT', '/* comment 5 \\*\\// */'],
        ['COMMENT', '// comment5\n'],
        ['IDENTIFIER', 'char'],
        ['IDENTIFIER', 's2'],
        ['STRING', '"asdjlsajdlksad"'],
        ['STRING', '"asdsajdlsad"'],
        ['COMMENT', '// \\\n                                   single line comment \\\n        with escapes\n'],
        ['IDENTIFIER', 'char'],
        ['IDENTIFIER', 'statement'],
    ])

    # https://en.cppreference.com/w/cpp/language/pack_indexing
    def test_cpp_templates(self):
        self.lex(r"""
template<typename... Ts>
constexpr auto f(Ts&&... ts) {
    return sizeof...(Ts);
}

template<typename T, T::t t = 0>
int f() {
    std::cout << t << std::endl;
    ns1::ns2::type v;
    ns1::ns2::type2<int> v2;
    ns1::ns2::type3<int, double> v3;
}
""", [
        ['IDENTIFIER', 'template'],
        ['IDENTIFIER', 'typename'],
        ['IDENTIFIER', 'Ts'],
        ['IDENTIFIER', 'constexpr'],
        ['IDENTIFIER', 'auto'],
        ['IDENTIFIER', 'f'],
        ['IDENTIFIER', 'Ts'],
        ['IDENTIFIER', 'ts'],
        ['IDENTIFIER', 'return'],
        ['IDENTIFIER', 'sizeof'],
        ['IDENTIFIER', 'Ts'],
        ['IDENTIFIER', 'template'],
        ['IDENTIFIER', 'typename'],
        ['IDENTIFIER', 'T'],
        ['IDENTIFIER', 'T'],
        ['IDENTIFIER', 't'],
        ['IDENTIFIER', 't'],
        ['IDENTIFIER', 'int'],
        ['IDENTIFIER', 'f'],
        ['IDENTIFIER', 'std'],
        ['IDENTIFIER', 'cout'],
        ['IDENTIFIER', 't'],
        ['IDENTIFIER', 'std'],
        ['IDENTIFIER', 'endl'],
        ['IDENTIFIER', 'ns1'],
        ['IDENTIFIER', 'ns2'],
        ['IDENTIFIER', 'type'],
        ['IDENTIFIER', 'v'],
        ['IDENTIFIER', 'ns1'],
        ['IDENTIFIER', 'ns2'],
        ['IDENTIFIER', 'type2'],
        ['IDENTIFIER', 'int'],
        ['IDENTIFIER', 'v2'],
        ['IDENTIFIER', 'ns1'],
        ['IDENTIFIER', 'ns2'],
        ['IDENTIFIER', 'type3'],
        ['IDENTIFIER', 'int'],
        ['IDENTIFIER', 'double'],
        ['IDENTIFIER', 'v3'],
    ])

    # https://en.cppreference.com/w/cpp/language/requires
    def test_cpp_concepts(self):
        self.lex(r"""
template<typename T>
concept C = requires(T x) {
    {x.count()} -> std::same_as<int>;
    requires Same<T*, decltype(&x)>
};
""", [
        ['IDENTIFIER', 'template'],
        ['IDENTIFIER', 'typename'],
        ['IDENTIFIER', 'T'],
        ['IDENTIFIER', 'concept'],
        ['IDENTIFIER', 'C'],
        ['IDENTIFIER', 'requires'],
        ['IDENTIFIER', 'T'],
        ['IDENTIFIER', 'x'],
        ['IDENTIFIER', 'x'],
        ['IDENTIFIER', 'count'],
        ['IDENTIFIER', 'std'],
        ['IDENTIFIER', 'same_as'],
        ['IDENTIFIER', 'int'],
        ['IDENTIFIER', 'requires'],
        ['IDENTIFIER', 'Same'],
        ['IDENTIFIER', 'T'],
        ['IDENTIFIER', 'decltype'],
        ['IDENTIFIER', 'x'],
    ])

    def test_cpp_class(self):
        self.lex(r"""
using namespace std;

auto f() -> std::string;

class test {
public:
    int operator ""_tx(int);
    int a = 123_tx;
};
""", [
        ['IDENTIFIER', 'using'],
        ['IDENTIFIER', 'namespace'],
        ['IDENTIFIER', 'std'],
        ['IDENTIFIER', 'auto'],
        ['IDENTIFIER', 'f'],
        ['IDENTIFIER', 'std'],
        ['IDENTIFIER', 'string'],
        ['IDENTIFIER', 'class'],
        ['IDENTIFIER', 'test'],
        ['IDENTIFIER', 'public'],
        ['IDENTIFIER', 'int'],
        ['IDENTIFIER', 'operator'],
        ['STRING', '""'],
        ['IDENTIFIER', '_tx'],
        ['IDENTIFIER', 'int'],
        ['IDENTIFIER', 'int'],
        ['IDENTIFIER', 'a'],
        ['IDENTIFIER', '_tx'],
    ])

    def test_cpp_attrs(self):
        self.lex(r"""
[[using test: atr1]] [[atr2]]
int f[[atr3]]();
""", [
        ['IDENTIFIER', 'using'],
        ['IDENTIFIER', 'test'],
        ['IDENTIFIER', 'atr1'],
        ['IDENTIFIER', 'atr2'],
        ['IDENTIFIER', 'int'],
        ['IDENTIFIER', 'f'],
        ['IDENTIFIER', 'atr3'],
    ])

    # https://en.cppreference.com/w/cpp/language/noexcept_spec
    def test_cpp_noexpect(self):
        self.lex(r"""
void f() noexpect(true) {}
""", [
        ['IDENTIFIER', 'void'],
        ['IDENTIFIER', 'f'],
        ['IDENTIFIER', 'noexpect'],
        ['IDENTIFIER', 'true'],
    ])

    # https://en.cppreference.com/w/cpp/language/coroutines
    def test_cpp_coroutines(self):
        self.lex(r"""
task<> test() {
    co_await test2();
}
""", [
        ['IDENTIFIER', 'task'],
        ['IDENTIFIER', 'test'],
        ['IDENTIFIER', 'co_await'],
        ['IDENTIFIER', 'test2'],
    ])

