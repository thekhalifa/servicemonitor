Service Monitor
===============

Live monitor for *systemd* units.

Queries Services, Timers and Sockets through the Manager interface on
DBus and supports starting, stopping, restarting or enabling/disabling
unit files.

**Note** this is an early release that hasn't had a lot of real world testing yet.
Help with testing and issues is very welcome through github

* https://github.com/thekhalifa/servicemonitor

.. image:: data/sm-screenshot.png


How to install
--------------
The most common way to install is from PPA respository if you're using a Debian based distro.

Install from PPA
^^^^^^^^^^^^^^^^
The quickest way to install is to add the PPA repository and install from there with:
::
    sudo add-apt-repository ppa:thekhalifa/ppa
    sudo apt-get update
    sudo apt-get install servicemonitor

Then you should find *Service Monitor* app in your app menu.

Alternatively you can download the .deb archives directly from
https://launchpad.net/~thekhalifa/+archive/ubuntu/ppa/+packages

Install manually
^^^^^^^^^^^^^^^^

It's a simple python application so there is no automake or meson or pip, but there is
supplied make script that will install a few files and icons for you
::
    git clone https://github.com/thekhalifa/servicemonitor
    cd servicemonitor
    sudo make manual-install

Then you should find *Service Monitor* app in your app menu.

The following dependecies should be pretty standard on systemd distros, but here is the list:

* python3 (>= 3.8)
* python3-gi (>= 3)
* dconf-gsettings-backend | gsettings-backend
* gir1.2-gtk-3.0 (>= 3.24)
* dbus (>= 1.12), systemd (>= 240)


Uninstall with the same make script (but it leaves the icons)
::
    sudo make uninstall


How to run locally
------------------
You can run the application from the current directly, but some icons will be missing
::
    chmod u+x servicemonitor-local.py   # if needed
    ./servicemonitor-local.py


Todo
----
* Move actions to separate thread so it doesn't block UI
* Info dialog: Add copy to clipboard for main treeview or info treeview

