# SPDX-License-Identifier: GPL-3.0-or-later

import datetime


class Unit(dict):
    suffix_ts = "Timestamp"
    suffix_tsmono = "TimestampMonotonic"
    suffix_us = "USec"
    suffix_usrt = "USecRealtime"
    negative_one_int = 18446744073709551615  # FFFFFFFF FFFFFFFF

    def __init__(self, name, path, description="", load="", state="", substate=""):
        self['Name'] = name
        self['Path'] = path
        self['Description'] = description
        self['Load'] = load
        self['State'] = state
        self['Substate'] = substate
        if '.' in self['Name']:
            n, t = name.split('.', 1)
            self['UnitType'] = t
            self[t.capitalize()] = n

    def getprop_fmt(self, prop):
        value = self.get(prop)
        if value is None and ' ' in prop:
            otherkey = prop.replace(' ', '')
            value = self.get(otherkey)

        if type(value) == list:
            value = str(value)
            if value:
                value = value.lstrip('[').rstrip(']')
        elif type(value) == tuple:
            value = str(value)
            if value:
                value = value.lstrip('(').rstrip(')')
        elif type(value) == int:
            if value == self.negative_one_int:
                value = "-1"
            elif prop.endswith(self.suffix_ts) and value > 1000000:
                value = str(datetime.datetime.fromtimestamp(value / (1000 * 1000)))
            elif prop.endswith(self.suffix_us) and value > 1000000:
                value = str(datetime.datetime.fromtimestamp(value / (1000 * 1000 * 1000)))
            elif prop.endswith(self.suffix_usrt) and value > 1000000:
                value = str(datetime.datetime.fromtimestamp(value / (1000 * 1000)))
            elif prop.endswith(self.suffix_tsmono) > 0:
                value = str(datetime.timedelta(microseconds=value))
            else:
                value = str(value)

        return value
