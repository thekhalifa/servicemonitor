# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from src.unit import Unit


class UnitTestCase(unittest.TestCase):
    def test_simple1(self):
        u = Unit("test1", "")
        self.assertEqual(u["Name"], "test1")
        self.assertEqual(u.getprop_fmt("Name"), "test1")
        self.assertEqual(u["Path"], "")
        self.assertEqual(u.getprop_fmt("Path"), "")
        self.assertEqual(u["Description"], "")
        self.assertEqual(u.getprop_fmt("Description"), "")
        self.assertIsNone(u.getprop_fmt("UNKNOWN"))
        self.assertIsNone(u.getprop_fmt("UnitType"))

    def test_simple2(self):
        u = Unit("test2.service", "/unit/test2_2e_service", "Test Service", "LOADED", "ACTIVE", "RUNNING")
        self.assertEqual(u["Name"], "test2.service")
        self.assertEqual(u["UnitType"], "service")
        self.assertEqual(u["Service"], "test2")
        self.assertEqual(u["Path"], "/unit/test2_2e_service")
        self.assertEqual(u["Load"], "LOADED")
        self.assertEqual(u["State"], "ACTIVE")
        self.assertEqual(u["Substate"], "RUNNING")

    def test_format1(self):
        u = Unit("test3.service", "Test Service")
        u["MultiWordParam"] = 5
        self.assertEqual(u["MultiWordParam"], 5)
        # self.assertIsNone(u["Multi Word Param"])
        self.assertEqual(u.getprop_fmt("MultiWordParam"), '5')
        self.assertEqual(u.getprop_fmt("Multi Word Param"), '5')
        print("Last one...........")


if __name__ == '__main__':
    unittest.main()
