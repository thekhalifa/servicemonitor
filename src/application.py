# SPDX-License-Identifier: GPL-3.0-or-later
import os.path
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from infodlg import InfoDialog
from preferences import PrefDialog, PrefStorage
from dbuscaller import DBusCaller
from unit import Unit

ABOUT_NAME = "Service Monitor"
ABOUT_VERSION = "v 0.1"
ABOUT_COPYRIGHT = "Copyright 2021 Ahmad Khalifa"
ABOUT_AUTHORS = ["Ahmad Khalifa"]
ABOUT_WEBSITE = "https://github.com/thekhalifa/servicemonitor"
ABOUT_ICON = "angry-eye"
ABOUT_COMMENT = "Live monitor for systemd units."
ABOUT_LICENSE = Gtk.License.GPL_3_0


class ServiceMonitor:
    run_dir = None
    helper_dir = None
    dbuscaller = DBusCaller()
    dbusready = False
    UI_FILE = "application.ui"
    UNIT_HELPER_CMD = 'unithelper.py'
    REFRESH_DBUS_WAIT = 1
    ICON_ENABLE_ON = "gtk-add"
    ICON_ENABLE_OFF = "gtk-remove"

    window = None
    search_entry = None
    action_toolbar = None
    status_label = None
    show_inactive = None
    winmaximized = False
    winposition = None
    pending_refresh = False

    include_all = False
    current_ui = None
    service_ui = {"unittype": "service",
                  "treeview": None,
                  "datastore": None,
                  "filter": None,
                  "statuslabel": None,
                  "searchterm": "",
                  "hidden_cols": []}

    timer_ui = {"unittype": "timer",
                "treeview": None,
                "datastore": None,
                "filter": None,
                "statuslabel": None,
                "searchterm": "",
                "hidden_cols": []}

    socket_ui = {"unittype": "socket",
                 "treeview": None,
                 "datastore": None,
                 "filter": None,
                 "statuslabel": None,
                 "searchterm": "",
                 "hidden_cols": []}
    # mapping for the treeview index:
    # 0: Name, 3: Substate, 4: Unit File State
    COL_NAME = 0
    COL_SUBSTATE = 3
    COL_UFSTATE = 4

    ui_columns = {
        "service": ["Name", "S", "State", "Substate", "Unit File State", "Type", "Fragment Path", "Description",
                    "Main PID"],
        "timer": ["Name", "S", "State", "Substate", "Unit File State", "Triggers", "LastTriggerUSec",
                  "NextElapseUSecRealtime", "Unit", "FragmentPath", "Description", "Timers Calendar", "Result"],
        "socket": ["Name", "S", "State", "Substate", "Unit File State", "Listen", "Triggers", "FileDescriptorName",
                   "FragmentPath", "Result", "N Accept", "N Connections", "Description"]}

    icon_column = {"S": "Substate"}
    icon_values = {"running": "sm-status-green",
                   "exited": "sm-status-grey",
                   "dead": "sm-status-grey",
                   "failed": "sm-sphere-red",
                   "listening": "sm-status-green",
                   "waiting": "sm-status-grey",
                   "unknown": "sm-status-black"}

    ui_detail_columns = {
        "service": ["UnitFileState", "Type", "FragmentPath", "MainPID"],
        "timer": ["Triggers", "LastTriggerUSec", "NextElapseUSecRealtime", "Unit", "FragmentPath", "TimersCalendar",
                  "Result"],
        "socket": ["Listen", "Triggers", "FileDescriptorName", "FragmentPath", "Result", "NAccept", "NConnections"]}

    def __init__(self, rundir, helperdir=None):
        self.run_dir = os.path.abspath(rundir)
        if helperdir is None:
            self.helper_dir = self.run_dir
        else:
            self.helper_dir = os.path.abspath(helperdir)

    def _getconvert_coltypes(self, unittype):
        columns = self.ui_columns[unittype]
        coltypes = [str for i in columns]
        colimage = ""
        if "S" in columns:
            colimage = "S"
        return columns, coltypes, colimage

    def buildui(self, unittype, uidict):
        # Get ui definition
        uicols, coltypes, colimage = self._getconvert_coltypes(unittype)
        if not uicols or not coltypes:
            return
        # Tree selection
        select = uidict["treeview"].get_selection()
        select.set_mode(Gtk.SelectionMode.SINGLE)
        select.connect("changed", self.on_tree_selection_change, unittype)
        select.unselect_all()

        # Build data store
        uidict["datastore"] = Gtk.ListStore()
        uidict["datastore"].set_column_types(coltypes)
        uidict["filter"] = uidict["datastore"].filter_new()
        uidict["filter"].set_visible_func(self.filter_data_func)
        uidict["treeview"].set_model(Gtk.TreeModelSort(model=uidict["filter"]))
        hidden_cols = uidict["hidden_cols"]
        for num, col in enumerate(uicols):
            if col in colimage:
                tvcolumn = Gtk.TreeViewColumn(col, Gtk.CellRendererPixbuf(), icon_name=num)
            else:
                tvcolumn = Gtk.TreeViewColumn(col, Gtk.CellRendererText(), text=num)
                tvcolumn.set_resizable(True)
                tvcolumn.set_sort_column_id(num)
            if col in hidden_cols:
                tvcolumn.set_visible(False)

            uidict["treeview"].append_column(tvcolumn)
        uidict["treeview"].get_model().set_sort_column_id(0, Gtk.SortType.ASCENDING)

    def refresh_ui(self):
        if not self.dbusready:
            print("refresh_ui - dbus not ready yet")
            return
        # remove all data
        self.current_ui["datastore"].clear()
        # refresh data
        unittype = self.current_ui["unittype"]
        columns = self.ui_columns[unittype]
        unitfilter = ["*." + unittype]
        statefilter = ['active']
        if self.include_all:
            statefilter = []
        unitlist = self.dbuscaller.list_details(statefilter, unitfilter, self.ui_detail_columns[unittype])
        totalunits = len(unitlist)
        print("refresh_ui - total units", totalunits)
        for u in unitlist:
            line = []
            for column in columns:
                if column in self.icon_column:
                    iconfield = self.icon_column[column]
                    iconsourcevalue = u.get(iconfield, "unknown")
                    iconname = self.icon_values.get(iconsourcevalue)
                    line.append(iconname)
                    pass
                else:
                    line.append(u.getprop_fmt(column))
            # line = list(u.getprop_fmt(c) for c in columns)
            self.current_ui["datastore"].append(line)
        self.status_label.set_label(f"Refreshed {totalunits} {unittype} units")

    def refresh_toolbar_state(self, select):
        model, row = select.get_selected()
        if not model or not row:
            self.toolbar_state()
            return
        name, substate, unitstate = model.get(row, 0, 3, 4)
        # print(f"-----: selection of {name} with substate {substate}")
        start = False
        stop = False
        restart = False
        enable = False
        info = True

        if substate == "exited" or substate == "failed" or substate == "dead":
            start = True

        if substate == "running":
            stop = True

        if substate != "waiting":
            restart = True

        if unitstate == "enabled":
            enable = "off"
        elif unitstate == "disabled":
            enable = "on"
        else:
            enable = False

        self.toolbar_state(start=start, stop=stop, restart=restart, enable=enable, info=info)

        # if substate == "running":
        #     self.toolbar_state(start=False, stop=True, restart=True, info=True)
        # elif substate == "exited":
        #     self.toolbar_state(start=True, stop=False, restart=True, info=True)
        # elif substate == "failed":
        #     self.toolbar_state(start=True, stop=False, restart=True, info=True)
        # elif substate == "dead":
        #     self.toolbar_state(start=True, stop=False, restart=True, info=True)
        # elif substate == "waiting":
        #     self.toolbar_state(start=False, stop=False, restart=False, info=True)
        # else:
        #     self.toolbar_state(start=False, stop=False, restart=False, info=True)

    def refresh_manager(self):
        if self.pending_refresh:
            return
        self.status_label.set_label("Updates in progress...")
        self.pending_refresh = True
        GLib.timeout_add_seconds(self.REFRESH_DBUS_WAIT, self.on_refresh_callback, None)

    def on_refresh_callback(self, *args):
        self.status_label.set_label("Refreshing list...")
        self.pending_refresh = False
        self.refresh_ui()

    def filter_data_func(self, model, iter, data):
        if not self.current_ui or not self.current_ui["searchterm"]:
            return True
        row = "".join(model[iter])
        if row.find(self.current_ui["searchterm"]) >= 0:
            return True
        return False

    # Tree Selection
    def on_tree_selection_change(self, select, data):
        # print("Event: on_tree_selection_change", select.get_tree_view().get_name(), data)
        self.refresh_toolbar_state(select)

    # Header bar actions
    def on_show_inactive_state_set(self, widget, data):
        print("Event: on_show_inactive_state_set to", data)
        self.include_all = data
        self.refresh_ui()

    def on_toprefresh_clicked(self, widget):
        print("Event: on_toprefresh_clicked")
        self.refresh_ui()

    # Search events
    def on_main_search_search_changed(self, widget):
        # print("Event: on_main_search_search_changed to", widget.get_text())
        self.current_ui["searchterm"] = widget.get_text()
        self.current_ui["filter"].refilter()

    def on_mainstack_set_focus_child(self, widget, data):
        # print("Event: on_mainstack_set_focus_child to", widget.get_name(), "data", type(data))
        boxname = widget.get_visible_child_name()
        # print("   --  box name:", boxname)
        if self.current_ui and self.current_ui["unittype"] == boxname:
            return
        elif boxname == "service":
            self.current_ui = self.service_ui
        elif boxname == "timer":
            self.current_ui = self.timer_ui
        elif boxname == "socket":
            self.current_ui = self.socket_ui
        else:
            return

        self.refresh_ui()
        self.current_ui["searchterm"] = self.search_entry.get_text()
        self.current_ui["filter"].refilter()

    def on_unitaction_clicked(self, widget):
        print("Event: on_unitaction_clicked - ", widget.get_name())
        action = widget.get_name()
        if action == "info-btn":
            self.show_info_dialog()
            return
        if action == "enable-btn":
            self.call_manager_helper()
            return

        unitmethod = ""
        if action == "start-btn":
            unitmethod = "Start"
        elif action == "stop-btn":
            unitmethod = "Stop"
        elif action == "restart-btn":
            unitmethod = "Restart"
        if not unitmethod:
            return
        self.call_unit_method(unitmethod)

    def on_preferences_clicked(self, widget):
        print("Event: on_preferences_clicked - ", widget.get_name())
        pref_dialog = PrefDialog(self.window, self.run_dir, self.service_ui["treeview"], self.timer_ui["treeview"],
                                 self.socket_ui["treeview"])
        pref_dialog.run()
        pref_dialog.destroy()
        # record hidden columns
        self.store_hidden_columns(self.service_ui)
        self.store_hidden_columns(self.timer_ui)
        self.store_hidden_columns(self.socket_ui)

    def on_about_clicked(self, *args):
        about = Gtk.AboutDialog(program_name=ABOUT_NAME, version=ABOUT_VERSION,
                                comments=ABOUT_COMMENT, website=ABOUT_WEBSITE,
                                license_type=ABOUT_LICENSE, copyright=ABOUT_COPYRIGHT,
                                authors=ABOUT_AUTHORS, logo_icon_name=ABOUT_ICON)
        about.run()
        about.destroy()

    # Main window
    def on_main_window_window_state_event(self, *args):
        self.winmaximized = self.window.is_maximized()

    def on_main_window_configure_event(self, *args):
        winx, winy = self.window.get_position()
        winw, winh = self.window.get_size()
        self.winposition = (winx, winy, winw, winh)

    def on_main_window_destroy(self, *args):
        self.dbuscaller.close_dbus()

        # save user settings
        print("saving settings...")
        PrefStorage.set(PrefStorage.SHOW_INACTIVE, self.include_all)
        PrefStorage.set(PrefStorage.WIN_MAXIMIZED, self.winmaximized)
        PrefStorage.set(PrefStorage.WIN_POSITION, self.winposition)
        PrefStorage.set(PrefStorage.HIDE_SERVICE_COL, self.service_ui["hidden_cols"])
        PrefStorage.set(PrefStorage.HIDE_TIMER_COL, self.timer_ui["hidden_cols"])
        PrefStorage.set(PrefStorage.HIDE_SOCKET_COL, self.socket_ui["hidden_cols"])

        # End it all
        Gtk.main_quit()

    def show_info_dialog(self):
        treeview = self.current_ui["treeview"]
        selection = treeview.get_selection()
        model, row = selection.get_selected()
        if not model or not row:
            print("Error, nothing selected for info")
            return
        name, *k = model.get(row, 0)
        if not name:
            print("Error, bad name for info")
            return
        unit = self.dbuscaller.unit_details(name)
        print(f"Full details {name}: ", len(unit))
        info_dialog = InfoDialog(self.window, name, unit)
        info_dialog.run()
        info_dialog.destroy()

    def call_unit_method(self, method):
        treeview = self.current_ui["treeview"]
        selection = treeview.get_selection()
        model, row = selection.get_selected()
        if not model or not row:
            print("Error, nothing selected for method")
            return
        name, *k = model.get(row, self.COL_NAME)
        if not name:
            print("Error, bad name for method")
            return

        response = False
        try:
            response = self.dbuscaller.unit_method(name, method)
        except gi.repository.GLib.GError as ge:
            print(f"Could not perform {method} on unit {name}, likely a permission issue", ge.message)

        if not response:
            msgdlg = Gtk.MessageDialog(transient_for=self.window, message_type=Gtk.MessageType.ERROR,
                                       buttons=Gtk.ButtonsType.OK, text=f"Could not perform {method}")
            msgdlg.format_secondary_text(f"Could not perform {method} on unit {name}")
            msgdlg.run()
            msgdlg.destroy()

    def call_manager_helper(self):
        treeview = self.current_ui["treeview"]
        selection = treeview.get_selection()
        model, row = selection.get_selected()
        if not model or not row:
            print("Error, nothing selected for method")
            return
        name, unitfilestate, *k = model.get(row, self.COL_NAME, self.COL_UFSTATE)
        if not name:
            print("Error, bad name for method")
            return
        if unitfilestate != "enabled" and unitfilestate != "disabled":
            print("Error, unit file state cannot be changed", unitfilestate)
            return

        response = False
        if unitfilestate == "enabled":
            action = "disable"
        elif unitfilestate == "disabled":
            action = "enable"

        argslist = ['pkexec', '--disable-internal-agent',
                    os.path.join(self.helper_dir, self.UNIT_HELPER_CMD), name, action]
        ps = subprocess.run(argslist, capture_output=True)
        if ps.returncode == 0:
            self.refresh_manager()
        else:
            output = ps.stdout.decode('utf-8')
            error = ps.stderr.decode('utf-8')
            print(f"Could not perform change unit file state for {name}")
            print(error)
            print(output)
            msgdlg = Gtk.MessageDialog(transient_for=self.window, message_type=Gtk.MessageType.ERROR,
                                       buttons=Gtk.ButtonsType.OK,
                                       text=f"Could not change unit file state {name}")
            msgdlg.format_secondary_text(output)
            msgdlg.run()
            msgdlg.destroy()

    def toolbar_state(self, start=False, stop=False, restart=False, enable=False, info=False):
        action_buttons = self.action_toolbar.get_children()
        # self.action_toolbar.foreach(lambda widget, data: widget.set_sensitive(False), None)
        for btn in action_buttons:
            name = btn.get_name()
            if name == "info-btn":
                btn.set_sensitive(info)
            elif name == "start-btn":
                btn.set_sensitive(start)
            elif name == "stop-btn":
                btn.set_sensitive(stop)
            elif name == "restart-btn":
                btn.set_sensitive(restart)
            elif name == "enable-btn":
                if enable == "on":
                    btn.set_icon_name(self.ICON_ENABLE_ON)
                    btn.set_sensitive(True)
                elif enable == "off":
                    btn.set_icon_name(self.ICON_ENABLE_OFF)
                    btn.set_sensitive(True)
                else:
                    btn.set_icon_name(self.ICON_ENABLE_OFF)
                    btn.set_sensitive(False)

    def store_hidden_columns(self, target_ui):
        treeview = target_ui["treeview"]
        if not treeview:
            return
        hidden_list = []
        treecols = treeview.get_columns()
        for col in treecols:
            title = col.get_title()
            if not col.get_visible():
                hidden_list.append(title)
        target_ui["hidden_cols"] = hidden_list

    def run(self):
        self.dbusready = self.dbuscaller.init_dbus()
        self.dbusready = self.dbuscaller.subscribe_signals(self.refresh_manager)

        self.toolbar_state()
        self.window.show_all()
        self.current_ui = self.service_ui
        self.refresh_ui()
        Gtk.main()

    def startup(self):
        # load user settings
        PrefStorage.load()

        builder = Gtk.Builder.new_from_file(os.path.join(self.run_dir, self.UI_FILE))
        builder.connect_signals(self)
        self.window = builder.get_object("main_window")
        self.window.set_title(ABOUT_NAME)
        self.service_ui["treeview"] = builder.get_object("treeview_services")
        self.timer_ui["treeview"] = builder.get_object("treeview_timers")
        self.socket_ui["treeview"] = builder.get_object("treeview_sockets")
        self.search_entry = builder.get_object("main_search")
        self.action_toolbar = builder.get_object("unitaction_toolbar")
        self.status_label = builder.get_object("status_label")
        self.show_inactive = builder.get_object("show_inactive")
        # load hidden columns and build the tree view
        self.service_ui["hidden_cols"] = PrefStorage.get(PrefStorage.HIDE_SERVICE_COL)
        print("Hidden cols: ", self.service_ui["hidden_cols"])
        self.buildui("service", self.service_ui)
        self.timer_ui["hidden_cols"] = PrefStorage.get(PrefStorage.HIDE_TIMER_COL)
        self.buildui("timer", self.timer_ui)
        self.socket_ui["hidden_cols"] = PrefStorage.get(PrefStorage.HIDE_SOCKET_COL)
        self.buildui("socket", self.socket_ui)

        ismaximised = PrefStorage.get(PrefStorage.WIN_MAXIMIZED)
        if ismaximised:
            self.window.maximize()
        isshowinactive = PrefStorage.get(PrefStorage.SHOW_INACTIVE)
        self.show_inactive.set_state(isshowinactive)
        self.include_all = isshowinactive
        winposition = PrefStorage.get(PrefStorage.WIN_POSITION)
        if winposition and len(winposition) == 4:
            winx, winy, winw, winh = winposition
            # load window dimensions and clamp them to monitor dimensions
            display = Gdk.Display().get_default()
            monitor = display.get_monitor_at_point(winx, winy)
            if not monitor:
                monitor = display.get_primary_monitor()
            if monitor:
                monrect = monitor.get_geometry()
                newx = winx if winx >= monrect.x else monrect.x
                newy = winy if winy >= monrect.y else monrect.y
                neww = winw if winw <= monrect.width else monrect.width
                newh = winh if winh <= monrect.height else monrect.height
                self.window.move(newx, newy)
                self.window.set_default_size(neww, newh)


if len(sys.argv) < 2:
    print("Missing lib dir, exiting")
    exit(1)
elif len(sys.argv) == 2:
    mainwindow = ServiceMonitor(sys.argv[1])
else:
    mainwindow = ServiceMonitor(sys.argv[1], sys.argv[2])

mainwindow.startup()
mainwindow.run()
