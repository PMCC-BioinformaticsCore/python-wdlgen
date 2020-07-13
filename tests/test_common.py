import unittest

from wdlgen import ParameterMeta


class TestParamMeta(unittest.TestCase):
    def test_quote_sanitise(self):
        meta = ParameterMeta(foo='"bar"').get_string()
        self.assertEqual('foo: "\\"bar\\""', meta)

    def test_nl_sanitise(self):
        meta = ParameterMeta(foo="bar\nbaz").get_string()
        self.assertEqual('foo: "bar\\nbaz"', meta)

    def test_backslackquote_sanitise(self):
        meta = ParameterMeta(foo='bar\\"').get_string()
        self.assertEqual('foo: "bar\\\\\\""', meta)
