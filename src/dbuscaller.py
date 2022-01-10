# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GLib
from unit import Unit


class DBusCaller:
    _LIVE_CALLS = True
    _CALL_TIMEOUT_MILLIS = 30000
    _ALLOWED_UNIT_METHODS = ['Start', 'Stop', 'Restart']
    _ALLOWED_MGR_METHODS = ['EnableUnitFiles', 'DisableUnitFiles']
    dbusconn = None
    mgrproxy = None
    pathproxies = {}
    signalsubs = None
    signal_refresh_cb = None

    dbus_prop = "org.freedesktop.DBus.Properties"
    msg_destination = "org.freedesktop.systemd1"
    mgr_path = "/org/freedesktop/systemd1"
    mgr_interface = "org.freedesktop.systemd1.Manager"

    iface_unit = "org.freedesktop.systemd1.Unit"
    iface_service = "org.freedesktop.systemd1.Service"
    iface_timer = "org.freedesktop.systemd1.Timer"
    iface_socket = "org.freedesktop.systemd1.Socket"

    def _is_connected(self):
        if self._LIVE_CALLS and self.dbusconn and not self.dbusconn.is_closed():
            return True
        return False

    def init_dbus(self):
        if self._is_connected() or not self._LIVE_CALLS:
            return True
        try:
            self.dbusconn = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            print("init_dbus: Connected to dbus", self.dbusconn.get_guid())
            return True
        except Exception as e:
            print("init_dbus: Error connecting to DBus", e)
            return False

    def close_dbus(self):
        if self.dbusconn and self._LIVE_CALLS:
            try:
                if self.signalsubs:
                    self.unsubscribe_signals()
                self.dbusconn.close_sync()
                self.dbusconn = None
                return True
            except Exception as e:
                print("_close_bus: Error closing DBus", e)

        return False

    def send_message(self, path, iface, method, argtype, args, reply_first_child=True):
        if not self._is_connected() or not self._LIVE_CALLS:
            return []

        result = self.dbusconn.call_sync(self.msg_destination, path, iface, method,
                                         GLib.Variant(argtype, args), None,
                                         Gio.DBusCallFlags.ALLOW_INTERACTIVE_AUTHORIZATION,
                                         -1, None)
        if result:
            if reply_first_child:
                return result[0]
            else:
                return result
        return []

    def getunitpath(self, unitname):
        """TODO: Should probably change to raising an exception instead of
            quietly suppressing it. Same for bad unitname arg"""
        if not unitname:
            return None
        try:
            path = self.send_message(self.mgr_path, self.mgr_interface, "GetUnit", "(s)", [unitname])
            return path
        except GLib.GError as ge:
            return None

    def getprops(self, unitpath, t="unit"):
        if not unitpath:
            return {}

        if t == "service":
            ifname = self.iface_service
        elif t == "timer":
            ifname = self.iface_timer
        elif t == "socket":
            ifname = self.iface_socket
        else:
            ifname = self.iface_unit

        try:
            return self.send_message(unitpath, self.dbus_prop, "GetAll", "(s)", [ifname])
        except GLib.GError as ge:
            # print("GError, code", ge.code, "message:", ge.message, "args:", ge.args)
            return {}

    def list_units(self, statelist=['active'], unitlist=['*.service']):
        units = []
        result = self.send_message(self.mgr_path, self.mgr_interface, "ListUnitsByPatterns",
                                   "(asas)", [GLib.Variant("as", statelist), GLib.Variant("as", unitlist)])
        for r in result:
            name, desc, load, status, sub, e1, path, num, *k = r
            # result format: [('cups.service', 'CUPS Scheduler',
            # 'loaded', 'active', 'running', '', #'/org/freedesktop/systemd1/unit/cups_2eservice', 0, '', '/')]
            u = Unit(name, path, desc, load, status, sub)
            units.append(u)
        return units

    def list_details(self, request_state, request_unit, detail_columns=[]):
        units = self.list_units(request_state, request_unit)
        if not detail_columns:
            return units

        for unit in units:
            # print("--Unit ", unit['Name'], ", path: ", unit['Path'])
            unitprops = self.getprops(unit['Path'])
            serviceprops = self.getprops(unit['Path'], unit['UnitType'])
            for col in detail_columns:
                if col in unitprops:
                    unit[col] = unitprops[col]
                elif col in serviceprops:
                    unit[col] = serviceprops[col]
        return units

    def unit_details(self, unitname):
        if not unitname:
            return None

        unitlist = self.list_units([], [unitname])
        if not unitlist:
            return None
        unit, *others = unitlist
        if others:
            print("ERROR, Received other units with same name: ", len(others))

        unitprops = self.getprops(unit['Path'])
        unit.update(unitprops)
        serviceprops = self.getprops(unit['Path'], unit['UnitType'])
        unit.update(serviceprops)
        return unit

    def subscribe_signals(self, refresh_cb):
        if not self._is_connected() or not self._LIVE_CALLS:
            return False

        print("Subscribing to manager signals...")
        self.signalsubs = self.dbusconn.signal_subscribe(None, "org.freedesktop.systemd1.Manager", None, None, None,
                                                         Gio.DBusSignalFlags.NONE, self.on_manager_signal, "DBCMgr")
        if self.signalsubs:
            if callable(refresh_cb):
                self.signal_refresh_cb = refresh_cb
            else:
                self.signal_refresh_cb = None
            return True
        return False

    def unsubscribe_signals(self):
        if self.signalsubs:
            self.dbusconn.signal_unsubscribe(self.signalsubs)
            return True
        return False

    def on_manager_signal(self, connection, sender, path, iface, signal, params, userdata):
        if userdata and userdata == "DBCMgr" and path == self.mgr_path:
            # print("DBusCaller: Manager signal being processed...")
            self.process_signal(signal, params)
        else:
            print("DBusCaller: ignoring manager signal on iface", iface, "and path", path)

    def process_signal(self, signal, params):
        if not signal or not self.signal_refresh_cb:
            print("DBusCaller: Skipping signal", signal, "params", params, "cb", self.signal_refresh_cb)
            return
        if signal == "Reloading":
            print("DBusCaller: [Reload]] signal")
            if params:
                value, *k = params
                if not value:
                    print("            -- Done")
                    self.signal_refresh_cb()
        elif signal == "JobNew":
            print("DBusCaller: [JobNew] signal, doing nothing.")
        elif signal == "JobRemoved":
            print("DBusCaller: [JobRemoved] signal, sending refresh call")
            self.signal_refresh_cb()
        elif signal == "UnitFilesChanged":
            print("DBusCaller: [UnitFilesChanged] signal, sending refresh call")
            self.signal_refresh_cb()
        elif signal == "UnitNew":
            print("DBusCaller: [UnitNew] signal, doing nothing.")
        elif signal == "UnitRemoved":
            print("DBusCaller: [UnitRemoved] signal, doing nothing.")
        else:
            print(f"DBusCaller: [Unknown] signal ({signal}), doing nothing.")

    def unit_method(self, unitname, method):
        if not unitname or not method:
            return False

        unitpath = self.getunitpath(unitname)
        if not unitpath:
            print("ERROR, invalid path for", unitname)
            return False
        if method not in self._ALLOWED_UNIT_METHODS:
            print("ERROR, method not allowed", method)
            return False

        jobid = self.send_message(unitpath, self.iface_unit, method, "(s)", ["fail"])
        print(f"DBusCaller: Response for [{method}] of [{unitname}]: jobid: {jobid}")
        return True

    def unit_file_enable(self, unitname):
        if not unitname:
            print("unit_file_enable: Error, bad unit name", unitname)
            return False
        return self.manager_method("EnableUnitFiles", "(asbb)", ([unitname], False, True))

    def unit_file_disable(self, unitname):
        if not unitname:
            print("unit_file_disable: Error, bad unit name", unitname)
            return False
        return self.manager_method("DisableUnitFiles", "(asb)", ([unitname], True))

    def manager_method(self, method, vartype, param):
        if not method or not vartype:
            print("DBusCaller: manager_method error, method or vartype missing", method, vartype)
            return False

        if method not in self._ALLOWED_MGR_METHODS:
            print("DBusCaller: manager_method error, method not allowed", method)
            return False

        response = self.send_message(self.mgr_path, self.mgr_interface, method, vartype, param, False)
        print(f"DBusCaller: Response for [{method}]: {repr(response)}")
        return True

    def __repr__(self):
        rep = f"{type(self)}\n"
        for d in dir(self):
            if d[0:2] == "__":
                continue
            rep += f"-- {d}\n"
        return rep

