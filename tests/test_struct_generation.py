import unittest

from wdlgen import WdlType, String, Int
from wdlgen.struct import Struct


class TestStructs(unittest.TestCase):
    def test_spec_example_1(self):
        s = Struct("Name")
        s.add_field(String, "myString")
        s.add_field(Int, "myInt")

        self.assertEqual(
            """\
struct Name {
  String myString
  Int myInt
}""",
            s.get_string(),
        )
