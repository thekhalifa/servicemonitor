# SPDX-License-Identifier: GPL-3.0-or-later

import time
import unittest

from unit import Unit
from dbuscaller import DBusCaller


class DBusCallerStateTestCase(unittest.TestCase):

    dc = DBusCaller()
    signalreceived = False

    @classmethod
    def setUpClass(cls):
        cls.dc.init_dbus()

    @classmethod
    def tearDownClass(cls):
        cls.dc.close_dbus()

    def test_connection(self):
        self.assertTrue(self.dc._is_connected())

    def test_listunits_all(self):
        result = self.dc.list_units(None, None)
        allcount = len(result)
        self.assertGreater(allcount, 10)
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], Unit)

        result = self.dc.list_units([], [])
        self.assertGreater(len(result), 10)
        self.assertEqual(len(result), allcount)
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], Unit)

    def test_listunits_none(self):
        result = self.dc.list_units([''], [])
        self.assertEqual(len(result), 0)
        result = self.dc.list_units([], [''])
        self.assertEqual(len(result), 0)

        result = self.dc.list_units([], [''])
        self.assertEqual(len(result), 0)
        result = self.dc.list_units([], [''])
        self.assertEqual(len(result), 0)

    def test_listunits_single(self):
        result = self.dc.list_units([], ['cups.service'])
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], Unit)
        self.assertEqual(result[0].getprop_fmt("Name"), "cups.service")
        self.assertRegex(result[0].getprop_fmt("Path"), "/.*/cups_2eservice")

    def test_listunits_filter(self):
        allresult = self.dc.list_units([], [])
        activeresult = self.dc.list_units(['active'], [])
        serviceresult = self.dc.list_units([], ['*.service'])
        activeserviceresult = self.dc.list_units(['active'], ['*.service'])
        self.assertGreater(len(allresult), len(activeresult))
        self.assertGreater(len(activeresult), len(activeserviceresult))
        self.assertGreater(len(allresult), len(serviceresult))
        self.assertGreater(len(serviceresult), len(activeserviceresult))

        result = self.dc.list_units([], ['cups.service', 'cups.socket'])
        self.assertEqual(len(result), 2)
        result = self.dc.list_units(None, ['cups.service', 'cups.socket'])
        self.assertEqual(len(result), 2)

    def test_unitpath(self):
        self.assertRegex(self.dc.getunitpath('cups.service'), "/.*/cups_2eservice")
        self.assertIsNone(self.dc.getunitpath('badvalue.service'))

    def test_unitpath(self):
        self.assertRegex(self.dc.getunitpath('cups.service'), "/.*/cups_2eservice")
        self.assertIsNone(self.dc.getunitpath('badvalue.service'))

    def test_unitprops(self):
        badresults = self.dc.getprops(None)
        self.assertIsInstance(badresults, dict)
        self.assertEqual(len(badresults), 0)

        badresults = self.dc.getprops('/asdflljkss/sdfsdf/sdf/sdf/unit/_2eservice')
        self.assertIsInstance(badresults, dict)
        self.assertEqual(len(badresults), 0)

        unitresults = self.dc.getprops('/org/freedesktop/systemd1/unit/cups_2eservice')
        self.assertIsInstance(unitresults, dict)

        unitresults2 = self.dc.getprops(self.dc.getunitpath('cups.service'), 'unit')
        self.assertIsInstance(unitresults, dict)
        self.assertEqual(len(unitresults), len(unitresults2))

        results = self.dc.getprops(self.dc.getunitpath('cups.service'), 'service')
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 10)

        results = self.dc.getprops(self.dc.getunitpath('cups.service'), 'socket')
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), 0)

    def test_list_details(self):
        service_details = ['Type', 'FragmentPath', 'Slice', 'ExecStart', 'ControlGroup']
        timer_details = ['Unit', 'Triggers', 'FragmentPath', 'LastTriggerUSec', 'NextElapseUSecRealtime']
        socket_details = ['Listen', 'Triggers', 'FileDescriptorName', 'FragmentPath']

        badresult = self.dc.list_details([''], [''])
        self.assertEqual(len(badresult), 0)

        # compare keys to a dummy unit
        dummyunit = Unit("dummyunit.service", "path")
        singleresult = self.dc.list_details(None, ['cups.service'])
        self.assertEqual(len(singleresult), 1)
        firstunit, *k = singleresult
        self.assertEqual(len(firstunit), len(dummyunit))
        for key in dummyunit:
            self.assertIn(key, firstunit)

        # add detail keys
        svcwithdetails, *k = self.dc.list_details(None, ['cups.service'], service_details)
        self.assertEqual(len(svcwithdetails), len(dummyunit) + len(service_details))
        for key in service_details:
            self.assertIn(key, svcwithdetails)

    def test_unit_details(self):
        badresult = self.dc.unit_details(None)
        self.assertIsNone(badresult)
        badresult = self.dc.unit_details('')
        self.assertIsNone(badresult)
        badresult = self.dc.unit_details('nonexistantservice.service')
        self.assertIsNone(badresult)

        result = self.dc.unit_details('cups.socket')
        self.assertIsInstance(result, Unit)
        self.assertGreater(len(result), 5)

    def test_subscribe_signals(self):
        self.assertTrue(self.dc.subscribe_signals(None))
        self.assertTrue(self.dc.unsubscribe_signals())
        time.sleep(1)

        self.signalreceived = False
        self.assertTrue(self.dc.subscribe_signals(self.signal_callback))
        self.assertFalse(self.signalreceived)

        self.dc.process_signal(None, None)
        self.assertFalse(self.signalreceived)
        self.dc.process_signal("Nothing", [])
        self.assertFalse(self.signalreceived)
        self.dc.process_signal("Reloading", ())
        self.assertFalse(self.signalreceived)
        self.dc.process_signal("Reloading", (True,))
        self.assertFalse(self.signalreceived)
        self.dc.process_signal("Reloading", (True, 0))
        self.assertFalse(self.signalreceived)
        self.dc.process_signal("Reloading", (False,))
        self.assertTrue(self.signalreceived)

        self.assertTrue(self.dc.unsubscribe_signals())

    def signal_callback(self):
        self.signalreceived = True

    def test_unit_method(self):
        self.assertFalse(self.dc.unit_method(None, None))
        self.assertFalse(self.dc.unit_method("cups.service", None))
        self.assertFalse(self.dc.unit_method("cups.service", "Kill"))
        self.assertFalse(self.dc.unit_method("cups.service", "RestartUnit"))
        self.assertTrue(self.dc.unit_method("cups.service", "Restart"))


if __name__ == '__main__':
    unittest.main()
