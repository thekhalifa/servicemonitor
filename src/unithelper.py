#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later

import subprocess
import sys
import os


class UnitHelper:
    """ Helper to run systemctl on behalf of the UI.
        Generally systemd will raise polkit authorization requests and they
        work, but the rest of the SysV chain may fail. So we execute the whole
        chain through a privileged execution.

        Using this instead of pkexec directly allows the Polkit dialog to explain
        to the user what is requesting the action (Vendor/message)
    """
    _sysctl_bin = "systemctl"
    _sysctl_version = "--version"

    def checksysctl(self):
        args = [self._sysctl_bin, self._sysctl_version]
        retcode, *k = self._run_sysctl(args)
        if retcode == 0:
            return True
        return False

    def _run_sysctl(self, args):
        retcode = 1
        sout = ""
        serr = ""
        if args and type(args) == list:
            try:
                ps = subprocess.run(args, capture_output=True)
                retcode = ps.returncode
                sout = ps.stdout
                serr = ps.stderr
            except FileNotFoundError:
                print("Error, systemctl Not found in path")
        else:
            print("Error, invalid arguments to run")
        output = sout.decode("utf-8")
        output += serr.decode("utf-8")
        return retcode, output

    def call_elevated_sysctl(self, unitname, action):
        if not unitname or not action:
            return False, "Error with unit name or action"
        argslist = [self._sysctl_bin, action, unitname]
        retcode, output = self._run_sysctl(argslist)
        return retcode, output


def main():
    print("System Gear Unit File helper")
    running_super = os.getuid() == 0

    if not running_super:
        print(f"Error, not running as privileged user")
        return 1
    if len(sys.argv) != 3:
        print(f"Error, invalid input arguments, expecting 2")
        return 1

    h = UnitHelper()
    if not h.checksysctl():
        print(f"Error, could not locate systemctl binary")
        return 1

    cmd, unitname, state = sys.argv
    if state not in ['enable', 'disable']:
        print(f"Error, invalid state argument '{state}'")
        return 1
    if not unitname.endswith('.service') and not unitname.endswith('.timer') and not unitname.endswith('.socket'):
        print(f"Error, invalid unit type in argument '{unitname}'")
        return 1

    print(f"Request to change {unitname} to {state}")
    ret, output = h.call_elevated_sysctl(unitname, state)
    if ret == 0:
        print(f"   Success")
    else:
        print(f"   Failed")
    print(output)
    return ret


if __name__ == "__main__":
    exit(main())
