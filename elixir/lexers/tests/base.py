import unittest

class LexerTest(unittest.TestCase):
    default_filtered_tokens = ("SPECIAL", "COMMENT", "STRING", "IDENTIFIER", "SPECIAL", "ERROR")

    # Checks if each token starts in the claimed position of code, if tokens cover all code and if no tokens overlap
    def verify_positions(self, code, tokens):
        last_token = None
        for t in tokens:
            if code[t.span[0]:t.span[1]] != t.token:
                self.fail(f"token {t} span != code span {code[t.span[0]:t.span[1]].encode()}")

            if last_token is not None and last_token.span[1] != t.span[0]:
                self.fail(f"token does not start where the previous token ends. prev: {last_token}, next: {t}")
            elif last_token is None and t.span[0] != 0:
                self.fail(f"first token does not start at zero: {t}")

            last_token = t

        if last_token.span[1] != len(code):
            self.fail(f"code is longer than position of the last token: {t}, code len: {len(code)}")

    # Checks if each token is in the claimed line of code
    def verify_lines(self, code, tokens):
        lines = [""] + code.split("\n") # zero line is emtpy
        last_line_number = None
        last_line_contents_left = None
        for t in tokens:
            if last_line_number != t.line:
                last_line_number = t.line
                last_line_contents_left = lines[t.line]

            if last_line_contents_left is None:
                self.fail(f"nothing left in line {t.line} for {t.token} {t}")

            newline_count = t.token.count("\n")
            all_token_lines = last_line_contents_left + "\n" + \
                    "\n".join([lines[i] for i in range(t.line+1, t.line+newline_count+1)]) + "\n"
            token_pos_in_lines = all_token_lines.find(t.token)
            if token_pos_in_lines == -1:
                self.fail(f"token {t.token} not found in line {t.line}: {all_token_lines.encode()}")
            if token_pos_in_lines < len(last_line_contents_left):
                last_line_contents_left = last_line_contents_left[token_pos_in_lines:]
            else:
                last_line_contents_left = None

    # Lex code, do basic soundness checks on tokens (lines and positions) and compare lexing results with a list of tokens
    def lex(self, code, expected, filtered_tokens=None, lexer_options={}):
        if filtered_tokens is None:
            filtered_tokens = self.default_filtered_tokens

        code = code.lstrip()
        tokens = list(self.lexer_cls(code, **lexer_options).lex())
        self.verify_positions(code, tokens)
        self.verify_lines(code, tokens)

        tokens = [[type.name, token] for type, token, span, line in tokens]
        tokens = [t for t in tokens if t[0] in filtered_tokens]
        try:
            self.assertEqual(tokens, expected)
        except Exception as e:
            print()
            for t in tokens: print(t, end=",\n")
            raise e

