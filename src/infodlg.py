# SPDX-License-Identifier: GPL-3.0-or-later

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class InfoDialog(Gtk.Dialog):
    """Info Dialog for details of a unit
        expects a Unit object which is a dict, but knows how to format the values
    """
    def __init__(self, parent, heading, unit):
        super().__init__(title=f"{heading} Properties", transient_for=parent, modal=True,
                         use_header_bar=True)
        self.set_default_size(400, 350)
        self.set_resizable(True)
        self.set_border_width(5)

        contentbox = self.get_content_area()
        contentbox.set_spacing(3)
        contentbox.set_border_width(5)

        liststore = Gtk.ListStore(str, str)
        liststore.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        for key in unit:
            liststore.append([key, unit.getprop_fmt(key)])

        treeview = Gtk.TreeView(model=liststore)
        keycol = Gtk.TreeViewColumn("Property", Gtk.CellRendererText(), text=0)
        valcol = Gtk.TreeViewColumn("Value", Gtk.CellRendererText(), text=1)
        treeview.append_column(keycol)
        treeview.append_column(valcol)
        treeview.set_headers_visible(False)
        scrollbox = Gtk.ScrolledWindow()
        scrollbox.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrollbox.add(treeview)
        contentbox.pack_start(scrollbox, True, True, 5)
        self.show_all()

