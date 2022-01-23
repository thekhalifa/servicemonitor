import os
import unittest

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from src.application import ServiceMonitor
from src.infodlg import InfoDialog
from src.preferences import PrefDialog, PrefStorage
from src.unit import Unit


class SystemMonitorTestCase(unittest.TestCase):

    src_dir = "src"

    @classmethod
    def setUpClass(cls):
        if os.getcwd().endswith("tests"):
            cls.src_dir = "../" + cls.src_dir

    def test_application_preferences_dialog(self):
        sm = ServiceMonitor("../src")
        sm.on_preferences_clicked(None)

    def test_application_about_dialog(self):
        sm = ServiceMonitor("../src")
        sm.on_about_clicked(None)

    def test_dummy_application(self):
        sm = ServiceMonitor("../src")
        sm.dbuscaller._LIVE_CALLS = False
        sm.run()

    def test_pref_dialog(self):
        treeview = Gtk.TreeView()
        tvcolumn1 = Gtk.TreeViewColumn("Name Column")
        tvcolumn2 = Gtk.TreeViewColumn("Description Column")
        treeview.append_column(tvcolumn1)
        treeview.append_column(tvcolumn2)
        pref_dlg = PrefDialog(None, "../src", treeview, treeview, treeview)
        pref_dlg.run()
        pref_dlg.destroy()

    def test_pref_storage(self):
        PrefStorage.load()
        self.assertIsNotNone(PrefStorage.get(PrefStorage.WIN_POSITION))
        self.assertIsNotNone(PrefStorage.get(PrefStorage.WIN_MAXIMIZED))
        self.assertIsNotNone(PrefStorage.get(PrefStorage.SHOW_INACTIVE))


    def test_info_dialog(self):
        unit1 = Unit("Major.service", "/path/to/major/", "Major Service", "loaded", "active", "running")
        info_dlg = InfoDialog(None, "MajorServiceTitle", unit1)
        info_dlg.run()
        info_dlg.destroy()


if __name__ == '__main__':
    unittest.main()
