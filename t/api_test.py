#!/usr/bin/env python3
import os
import sys

from falcon import testing

api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','api'))
sys.path.insert(0, api_dir)

from api import create_ident_getter

class APITest(testing.TestCase):
    def setUp(self):
        super(APITest, self).setUp()

        self.app = create_ident_getter()

class TestMyApp(APITest):
    def test_identifier_not_found(self):
        result = self.simulate_get('/ident/tree/SOME_NONEXISTENT_IDENTIFIER', query_string="version=latest")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json, {'definitions': [], 'references':[]})