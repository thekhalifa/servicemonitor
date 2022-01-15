# SPDX-License-Identifier: GPL-3.0-or-later

import datetime


class Unit(dict):
    suffix_ts = "Timestamp"
    # suffix_tsmono = "TimestampMonotonic"
    suffix_us = "USec"
    suffix_usrt = "USecRealtime"
    suffix_dirmode = "DirectoryMode"

    negative_notset = "[not set]"
    negative_one_int64 = 0xFFFFFFFFFFFFFFFF  # 18446744073709551615
    negative_one_int32 = 0xFFFFFFFF

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

        if isinstance(value, list):
            if value and (isinstance(value[0], str) or isinstance(value[0], tuple)):
                value = str(value).lstrip('[').rstrip(']')
            elif value:
                value = str(value).lstrip('[').rstrip(']')
            else:
                value = ""
        elif isinstance(value, tuple):
            value = str(value)
            if value:
                value = value.lstrip('(').rstrip(')')
        elif isinstance(value, int):
            if value == self.negative_one_int64 or value == self.negative_one_int32:
                value = self.negative_notset
            elif prop.endswith(self.suffix_ts) and value > 1000000:
                dt = datetime.datetime.fromtimestamp(int(value / (1000 * 1000)))
                value = str(dt)
            elif prop.endswith(self.suffix_us):
                # format microseconds as us, ms, s or higher. drop the decimal if it's 0
                if value < 1000:
                    value = f"{value:.0f}us" if value % 1 == 0 else f"{value:.1f}us"
                elif value < 1000000:  # 1s
                    value = value/1000
                    value = f"{value:.0f}ms" if value % 1 == 0 else f"{value:.1f}ms"
                elif value < 60000000:
                    value = value / 1000000
                    value = f"{value:.0f}s" if value % 1 == 0 else f"{value:.1f}s"
                elif value < 31536000000000:    # 1 year (31536000) in us
                    value = str(datetime.timedelta(microseconds=value))
                else:   # more than 1 year, format as a date
                    value = str(datetime.datetime.fromtimestamp(value / (1000 * 1000)))
            elif prop.endswith(self.suffix_usrt) and value > 1000000:
                value = str(datetime.datetime.fromtimestamp(value / (1000 * 1000)))
            elif prop.endswith(self.suffix_dirmode):
                value = f"{value:04o}"
            else:
                value = str(value)
        elif not isinstance(value, str):
            value = str(value)
        return value
