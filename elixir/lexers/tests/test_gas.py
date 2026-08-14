from ..lexers import GasLexer
from .base import LexerTest

class GasLexerTest(LexerTest):
    lexer_cls = GasLexer
    default_filtered_tokens = ("SPECIAL", "COMMENT", "STRING", "IDENTIFIER", "SPECIAL", "ERROR")

    def test_comments_m68k(self):
        self.lex(r"""
# comment 1
#comment 2
    clrl d1 | comment 3
    clrl d0 |comment 4
| comment 4

    clrl d2 # comment 3

#if defined(C1) || !defined(C2)
	addql #4,%sp
label:
	movel	#-IDNENT,%sp@(IDENT)| comment 5
// /linux/v6.10.7/source/arch/m68k/ifpsp060/src/fplsp.S
    test # comment 6
# endif

#define macro(x) inst &IDENT,%pc@(ident); inst x
""", [
        ['COMMENT', '# comment 1\n'],
        ['COMMENT', '#comment 2\n'],
        ['IDENTIFIER', 'clrl'],
        ['IDENTIFIER', 'd1'],
        ['COMMENT', '| comment 3\n'],
        ['IDENTIFIER', 'clrl'],
        ['IDENTIFIER', 'd0'],
        ['COMMENT', '|comment 4\n'],
        ['COMMENT', '| comment 4\n'],
        ['IDENTIFIER', 'clrl'],
        ['IDENTIFIER', 'd2'],
        ['COMMENT', '# comment 3\n'],
        ['SPECIAL', '#if'],
        ['IDENTIFIER', 'defined'],
        ['IDENTIFIER', 'C1'],
        ['IDENTIFIER', 'defined'],
        ['IDENTIFIER', 'C2'],
        ['IDENTIFIER', 'addql'],
        ['IDENTIFIER', 'sp'],
        ['IDENTIFIER', 'label'],
        ['IDENTIFIER', 'movel'],
        ['IDENTIFIER', 'IDNENT'],
        ['IDENTIFIER', 'sp'],
        ['IDENTIFIER', 'IDENT'],
        ['COMMENT', '| comment 5\n'],
        ['COMMENT', '// /linux/v6.10.7/source/arch/m68k/ifpsp060/src/fplsp.S\n'],
        ['IDENTIFIER', 'test'],
        ['COMMENT', '# comment 6\n'],
        ['SPECIAL', '# endif'],
        ['SPECIAL', '#define'],
        ['IDENTIFIER', 'macro'],
        ['IDENTIFIER', 'x'],
        ['IDENTIFIER', 'inst'],
        ['IDENTIFIER', 'IDENT'],
        ['IDENTIFIER', 'pc'],
        ['IDENTIFIER', 'ident'],
        ['IDENTIFIER', 'inst'],
        ['IDENTIFIER', 'x'],
    ], lexer_options={"arch": "m68k"})

    def test_comments_sparc(self):
        self.lex(r"""
#define F(i) 		\
	.type	i,@function;

    std	t1, [0x00];

/*comment default */
//comment default2
    .type identifier,#function
label:
        sethi   %hi(IDENT), %g0 !test comment
        wrpr %g1, %sp   ! test comment
# comment
#comment
        sethi   %hi(IDENT_1 | IDENT_2), %l0
""", [
        ['SPECIAL', '#define'],
        ['IDENTIFIER', 'F'],
        ['IDENTIFIER', 'i'],
        ['IDENTIFIER', 'type'],
        ['IDENTIFIER', 'i'],
        ['IDENTIFIER', 'function'],
        ['IDENTIFIER', 'std'],
        ['IDENTIFIER', 't1'],
        ['COMMENT', '/*comment default */'],
        ['COMMENT', '//comment default2\n'],
        ['IDENTIFIER', 'type'],
        ['IDENTIFIER', 'identifier'],
        ['IDENTIFIER', 'function'],
        ['IDENTIFIER', 'label'],
        ['IDENTIFIER', 'sethi'],
        ['IDENTIFIER', 'hi'],
        ['IDENTIFIER', 'IDENT'],
        ['IDENTIFIER', 'g0'],
        ['COMMENT', '!test comment\n'],
        ['IDENTIFIER', 'wrpr'],
        ['IDENTIFIER', 'g1'],
        ['IDENTIFIER', 'sp'],
        ['COMMENT', '! test comment\n'],
        ['COMMENT', '# comment\n'],
        ['COMMENT', '#comment\n'],
        ['IDENTIFIER', 'sethi'],
        ['IDENTIFIER', 'hi'],
        ['IDENTIFIER', 'IDENT_1'],
        ['IDENTIFIER', 'IDENT_2'],
        ['IDENTIFIER', 'l0'],
    ], lexer_options={"arch": "sparc"})

    def test_comments_arm32(self):
        self.lex(r"""
// comment default
/* comment default2 */
test:
    bic	r0, r1, #10
    # comment 1
    #comment 1
"""
+ "\t# comment 1" + r"""
	moveq	r0, #IDENTIFIER @ Comment
# comment 2
#comment 2
    push {r0}
    add \addr, \addr, \tmp  @comment3
    ldr r1, =TEST3
	ldr TEST, [sp, IDENT(i)];
	.long   PMD_TYPE_SECT | \
		PMD_BIT4
    stmfd	sp!, {r0, r1, r2, r3}
    eor RT0, d, b;
""", [
        ['COMMENT', '// comment default\n'],
        ['COMMENT', '/* comment default2 */'],
        ['IDENTIFIER', 'test'],
        ['IDENTIFIER', 'bic'],
        ['IDENTIFIER', 'r0'],
        ['IDENTIFIER', 'r1'],
        ['NUMBER', '10'],
        ['COMMENT', '# comment 1\n'],
        ['COMMENT', '#comment 1\n'],
        ['COMMENT', '# comment 1\n'],
        ['IDENTIFIER', 'moveq'],
        ['IDENTIFIER', 'r0'],
        ['IDENTIFIER', 'IDENTIFIER'],
        ['COMMENT', '@ Comment\n'],
        ['COMMENT', '# comment 2\n'],
        ['COMMENT', '#comment 2\n'],
        ['IDENTIFIER', 'push'],
        ['IDENTIFIER', 'r0'],
        ['IDENTIFIER', 'add'],
        ['IDENTIFIER', 'addr'],
        ['IDENTIFIER', 'addr'],
        ['IDENTIFIER', 'tmp'],
        ['COMMENT', '@comment3\n'],
        ['IDENTIFIER', 'ldr'],
        ['IDENTIFIER', 'r1'],
        ['IDENTIFIER', 'TEST3'],
        ['IDENTIFIER', 'ldr'],
        ['IDENTIFIER', 'TEST'],
        ['IDENTIFIER', 'sp'],
        ['IDENTIFIER', 'IDENT'],
        ['IDENTIFIER', 'i'],
        ['IDENTIFIER', 'long'],
        ['IDENTIFIER', 'PMD_TYPE_SECT'],
        ['IDENTIFIER', 'PMD_BIT4'],
        ['IDENTIFIER', 'stmfd'],
        ['IDENTIFIER', 'sp'],
        ['IDENTIFIER', 'r0'],
        ['IDENTIFIER', 'r1'],
        ['IDENTIFIER', 'r2'],
        ['IDENTIFIER', 'r3'],
        ['IDENTIFIER', 'eor'],
        ['IDENTIFIER', 'RT0'],
        ['IDENTIFIER', 'd'],
        ['IDENTIFIER', 'b'],
    ], self.default_filtered_tokens + ("NUMBER",), {"arch": "arm32"})

    def test_comments_generic(self):
        self.lex(r"""
/* comment
 * more comment
 * more comment
 */
    mov r0, r1  //test
    mov x0, #IDENT
    stp     x1, x2, [sp, #-4]!
#if defined(IDENT1) || defined(IDENT2)
#endif
""", [
        ['COMMENT', '/* comment\n * more comment\n * more comment\n */'],
        ['IDENTIFIER', 'mov'],
        ['IDENTIFIER', 'r0'],
        ['PUNCTUATION', ','],
        ['IDENTIFIER', 'r1'],
        ['COMMENT', '//test\n'],
        ['IDENTIFIER', 'mov'],
        ['IDENTIFIER', 'x0'],
        ['PUNCTUATION', ','],
        ['PUNCTUATION', '#'],
        ['IDENTIFIER', 'IDENT'],
        ['IDENTIFIER', 'stp'],
        ['IDENTIFIER', 'x1'],
        ['PUNCTUATION', ','],
        ['IDENTIFIER', 'x2'],
        ['PUNCTUATION', ','],
        ['PUNCTUATION', '['],
        ['IDENTIFIER', 'sp'],
        ['PUNCTUATION', ','],
        ['PUNCTUATION', '#'],
        ['PUNCTUATION', '-'],
        ['NUMBER', '4'],
        ['PUNCTUATION', ']'],
        ['PUNCTUATION', '!'],
        ['SPECIAL', '#if'],
        ['IDENTIFIER', 'defined'],
        ['PUNCTUATION', '('],
        ['IDENTIFIER', 'IDENT1'],
        ['PUNCTUATION', ')'],
        ['PUNCTUATION', '||'],
        ['IDENTIFIER', 'defined'],
        ['PUNCTUATION', '('],
        ['IDENTIFIER', 'IDENT2'],
        ['PUNCTUATION', ')'],
        ['SPECIAL', '#endif'],
    ], self.default_filtered_tokens + ("PUNCTUATION", "NUMBER"))

    def test_comments_preproc(self):
        self.lex(r"""
 # error "test"
#warning "test"
#include "test.h"
#include <test.h>
#if defined(T1) || defined(T2)
#endif
""", [
        ['SPECIAL', '# error "test"\n'],
        ['SPECIAL', '#warning "test"\n'],
        ['SPECIAL', '#include "test.h"'],
        ['SPECIAL', '#include <test.h>'],
        ['SPECIAL', '#if'],
        ['IDENTIFIER', 'defined'],
        ['IDENTIFIER', 'T1'],
        ['IDENTIFIER', 'defined'],
        ['IDENTIFIER', 'T2'],
        ['SPECIAL', '#endif'],
    ])

    def test_comments_literals(self):
        self.lex(r"""
.byte 12, 0b1010, 0B1010, 0x34, 0123, 0X45, 'a, '\b
.ascii "asdsad\"zxczc"
.float 0f-12321321030982394324\
        21321432432.234324324E-14
.float 0f-123.123213e+13
.float 0e-123.123213e+13
""", [
        ['IDENTIFIER', 'byte'],
        ['NUMBER', '12'],
        ['NUMBER', '0b1010'],
        ['NUMBER', '0B1010'],
        ['NUMBER', '0x34'],
        ['NUMBER', '0123'],
        ['NUMBER', '0X45'],
        ['STRING', "'a"],
        ['STRING', "'\\b"],
        ['IDENTIFIER', 'ascii'],
        ['STRING', '"asdsad\\"zxczc"'],
        ['IDENTIFIER', 'float'],
        ['NUMBER', '0f-12321321030982394324\\\n        21321432432.234324324E-14'],
        ['IDENTIFIER', 'float'],
        ['NUMBER', '0f-123.123213e+13'],
        ['IDENTIFIER', 'float'],
        ['NUMBER', '0e-123.123213e+13'],
    ], self.default_filtered_tokens + ("NUMBER",))

