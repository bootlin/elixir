if __name__ == "__main__":
    import sys
    from . import lexers

    if not (len(sys.argv) == 2 or (len(sys.argv) == 3 and sys.argv[1] == '-s')):
        print("usage:", sys.argv[0], "[-s]", "path/to/file")
        exit(1)

    short = sys.argv[1] == '-s'

    filename = sys.argv[-1]

    with open(filename) as f:
        if filename.endswith(('.c', '.h', '.cpp', '.hpp')):
            lexer = lexers.CLexer(f.read())
        elif filename.endswith(('.dts', '.dtsi')):
            lexer = lexers.DTSLexer(f.read())
        else:
            raise Exception("no lexer for filetype")

        for token in lexer.lex():
            if not short:
                print(token.line, token.token_type.name, token.span, token.token.encode())
            else:
                if token.token_type.name == 'IDENTIFIER' or token.token_type.name == 'STRING':
                    print(f"|{token.token}|", end='')
                else:
                    print(token.token, end='')

