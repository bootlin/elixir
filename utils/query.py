from elixir.query import Query
from elixir import lib

def cmd_stats(q, **kwargs):
    print("Versions: ", len(q.db.vers))
    print("Blobs: ", len(q.db.blob))
    if len(q.db.blob) != len(q.db.hash) or len(q.db.hash) != len(q.db.file):
        print("Warning, number of blobs, hashes or files is not equal")
    print("Definitions: ", len(q.db.defs))
    print("References: ", len(q.db.refs))

def cmd_versions(q, **kwargs):
    for major in q.get_versions().values():
        for minor in major.values():
            for v in minor:
                print(v)

def cmd_ident(q, version, ident, family, **kwargs):
    symbol_definitions, symbol_references, symbol_doccomments = q.search_ident(version, ident, family)
    print("Symbol Definitions:")
    for symbol_definition in symbol_definitions:
        print(symbol_definition)

    print("\nSymbol References:")
    for symbol_reference in symbol_references:
        print(symbol_reference)

    print("\nDocumented in:")
    for symbol_doccomment in symbol_doccomments:
        print(symbol_doccomment)

def cmd_file(q, version, path, **kwargs):
    code = q.get_tokenized_file(version, path)
    print(code)

if __name__ == "__main__":
    import argparse

    query = Query(lib.getDataDir(), lib.getRepoDir())

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    ident_subparser = subparsers.add_parser('stats', help="Get basic database stats")
    ident_subparser.set_defaults(func=cmd_stats, q=query)

    ident_subparser = subparsers.add_parser('versions', help="Get list of versions in the project")
    ident_subparser.set_defaults(func=cmd_versions, q=query)

    ident_subparser = subparsers.add_parser('ident', help="Get definitions and references of an identifier")
    ident_subparser.add_argument("version", help="The version of the project", type=str, default="latest")
    ident_subparser.add_argument('ident', type=str, help="The name of the identifier")
    ident_subparser.add_argument('family', type=str, help="The file family requested")
    ident_subparser.set_defaults(func=cmd_ident, q=query)

    file_subparser = subparsers.add_parser('file', help="Get a source file")
    file_subparser.add_argument("version", help="The version of the project", type=str, default="latest")
    file_subparser.add_argument('path', type=str, help="The path of the source file")
    file_subparser.set_defaults(func=cmd_file, q=query)

    args = parser.parse_args()
    args.func(**vars(args))

