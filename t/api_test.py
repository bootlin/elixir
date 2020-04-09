#!/usr/bin/env python3
import os
import sys

import falcon
from falcon import testing

api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','api'))
sys.path.insert(0, api_dir)

from api import create_ident_getter

class APITest(testing.TestCase):
    def setUp(self):
        super(APITest, self).setUp()

        self.app = create_ident_getter()

    def test_identifier_not_found(self):
        result = self.simulate_get('/ident/tree/SOME_NONEXISTENT_IDENTIFIER', query_string="version=latest")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json, {'definitions': [], 'references':[]})

    def test_missing_version(self):
        # A get request without a version query string
        result = self.simulate_get('/ident/tree/of_i2c_get_board_info')

        self.assertEqual(result.status_code, 400)

        required_response = falcon.HTTPMissingParam('version')
        self.assertEqual(result.json["title"], required_response.title)
        self.assertEqual(result.json["description"], required_response.description)

    def test_existing_identifier(self):
        result_for_specific_version = self.simulate_get('/ident/tree/of_i2c_get_board_info', query_string="version=v5.4")
        result_for_latest_version = self.simulate_get('/ident/tree/of_i2c_get_board_info', query_string="version=latest")

        expected_json = {
            'definitions': 
            [
                {'path': 'drivers/i2c/i2c-core-of.c', 'line': 22, 'type': 'function'},
                {'path': 'drivers/i2c/i2c-core-of.c', 'line': 62, 'type': 'variable'},
                {'path': 'include/linux/i2c.h', 'line': 968, 'type': 'function'},
                {'path': 'include/linux/i2c.h', 'line': 941, 'type': 'prototype'}
            ], 
            'references': 
                [
                    {'path': 'drivers/i2c/i2c-core-of.c', 'line': '22,62,73', 'type': None},
                    {'path': 'include/linux/i2c.h', 'line': '941,968', 'type': None}
                ]
            }
        
        self.assertEqual(result_for_specific_version.status_code, 200)
        self.assertEqual(result_for_latest_version.status_code, 200)
        
        self.assertEqual(result_for_specific_version.json, expected_json)
        self.assertEqual(result_for_latest_version.json, expected_json)