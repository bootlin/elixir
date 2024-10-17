if __name__ == "__main__":
    import sys
    from . import lexers

    if len(sys.argv) != 2:
        print("usage:", sys.argv[0], "path/to/file")
        exit(1)

    with open(sys.argv[1]) as f:
        lexer = lexers.CLexer(f.read())
        for token in lexer.lex():
            print(token.line, token.token_type.name, token.span, token.token.encode())

