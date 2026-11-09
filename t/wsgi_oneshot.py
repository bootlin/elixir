#!/usr/bin/env python3

#  This file is part of Elixir, a source code cross-referencer.
#
#  Elixir is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

"""Serve one WSGI request and write a CGI-style response.

The prove suite used to execute a CGI front end. The application is now a
Falcon WSGI app, so tests set REQUEST_URI and run this helper instead.
"""

import os
import sys
from wsgiref.util import setup_testing_defaults

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from elixir.web import application


def main():
    uri = os.environ.get('REQUEST_URI', '/')
    path, _, query = uri.partition('?')

    environ = {}
    setup_testing_defaults(environ)
    environ['REQUEST_METHOD'] = os.environ.get('REQUEST_METHOD', 'GET')
    environ['PATH_INFO'] = path
    environ['QUERY_STRING'] = query
    environ['REQUEST_URI'] = uri
    environ['RAW_URI'] = uri
    for key, value in os.environ.items():
        if key.startswith('LXR_') or key == 'ELIXIR_VERSION':
            environ[key] = value

    captured = {}

    def start_response(status, headers, exc_info=None):
        captured['status'] = status
        captured['headers'] = list(headers)
        return lambda data: None

    chunks = application(environ, start_response)
    try:
        body = b''.join(chunks)
    finally:
        close = getattr(chunks, 'close', None)
        if close is not None:
            close()

    print('Status: ' + captured['status'])
    for name, value in captured['headers']:
        if name.lower() == 'content-type':
            name = 'Content-Type'
        print(f'{name}: {value}')
    sys.stdout.write('\n')
    sys.stdout.flush()
    sys.stdout.buffer.write(body)


if __name__ == '__main__':
    main()
