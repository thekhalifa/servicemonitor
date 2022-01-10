# SPDX-License-Identifier: GPL-3.0-or-later

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib


class PrefDialog:
    """ Main Preferences Dialog
    """
    mainwindow = None

    def __init__(self, parent, rundir, servicetree, timertree, sockettree):
        super().__init__()

        # builder = Gtk.Builder.new_from_file("preferences.ui")
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(rundir, "preferences.ui"))
        self.prefdialog = builder.get_object("preferences_dialog")

        servicecol_treeview = builder.get_object("servicecolumn_treeview")
        timercol_treeview = builder.get_object("timercolumn_treeview")
        socketcol_treeview = builder.get_object("socketcolumn_treeview")
        self.sourcetrees = {"service": servicetree,
                            "timer": timertree,
                            "socket": sockettree}
        # populate columns
        self.targetmodel = {}
        self.populate_treeview_from_treecolumns(servicecol_treeview, servicetree, "service")
        self.populate_treeview_from_treecolumns(timercol_treeview, timertree, "timer")
        self.populate_treeview_from_treecolumns(socketcol_treeview, sockettree, "socket")

        self.notebook = builder.get_object("columns_notebook")
        self.prefdialog.show_all()

    def run(self):
        return self.prefdialog.run()

    def destroy(self):
        self.prefdialog.destroy()

    def populate_treeview_from_treecolumns(self, targettree, sourcetree, treetype):
        if not targettree or not sourcetree:
            print("populate exit:", targettree is None, sourcetree is None)
            return

        liststore = Gtk.ListStore(bool, str, int)
        if type(sourcetree) is list:
            print("populate dummy data")
            liststore.append([True, "First Row", 0])
            liststore.append([False, "Second Row", 1])
            liststore.append([False, "Third Longer Row", 2])
        else:
            treecols = sourcetree.get_columns()
            print("populate cols: ", len(treecols))
            for index, col in enumerate(treecols):
                title = col.get_title()
                visible = col.get_visible()
                liststore.append([visible, title, index])

        targettree.set_model(liststore)
        self.targetmodel[treetype] = liststore
        rendr = Gtk.CellRendererToggle()
        rendr.connect("toggled", self.on_columnstate_toggle, treetype)
        visiblecol = Gtk.TreeViewColumn("Visible", rendr, active=0)
        visiblecol.set_clickable(True)
        targettree.append_column(visiblecol)
        titlecol = Gtk.TreeViewColumn("Column Name", Gtk.CellRendererText(), text=1)
        targettree.append_column(titlecol)
        targettree.set_headers_visible(False)

    def on_columnstate_toggle(self, cell, path, data):
        print("PrefEvent: on_columnstate_toggle", cell, path, data)
        column_name = self.targetmodel[data][path][1]
        column_index = self.targetmodel[data][path][2]
        print(f"---------: column {column_name} at index {column_index}")
        newstate = not self.targetmodel[data][path][0]
        self.targetmodel[data][path][0] = newstate
        sourcetree = self.sourcetrees[data]
        if sourcetree:
            treecol = sourcetree.get_column(column_index)
            treecol.set_visible(newstate)


class PrefStorage:

    SHOW_INACTIVE = 'showinactive'
    WIN_MAXIMIZED = 'winmaximized'
    WIN_POSITION = 'winposition'
    HIDE_SERVICE_COL = 'hide-service-cols'
    HIDE_TIMER_COL = 'hide-timer-cols'
    HIDE_SOCKET_COL = 'hide-socket-cols'

    SETTINGS_SCHEMA = "ak.systemgear"
    KEY_VTYPES = {SHOW_INACTIVE: "b",
                  WIN_MAXIMIZED: "b",
                  WIN_POSITION: '(iiii)',
                  HIDE_SERVICE_COL: 'as',
                  HIDE_TIMER_COL: 'as',
                  HIDE_SOCKET_COL: 'as'}
    settings = None

    @classmethod
    def load(cls):
        cls.settings = Gio.Settings(schema=cls.SETTINGS_SCHEMA)

    @classmethod
    def get(cls, key):
        if cls.settings and key in cls.KEY_VTYPES:
            try:
                value = cls.settings.get_value(key)
                return value.unpack()
            except TypeError as e:
                print("TypeError getting value for key", key)
        return ""

    @classmethod
    def set(cls, key, value):
        if not cls.settings or key not in cls.KEY_VTYPES:
            return
        cls.settings.set_value(key, GLib.Variant(cls.KEY_VTYPES[key], value))

