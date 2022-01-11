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
As this uses python3 and queries DBus through GLib, the following dependencies
are needed:

* python3
* python3-gi (gobject-introspection)

You can install it with the supplied make script
::
    git clone https://github.com/thekhalifa/servicemonitor
    cd servicemonitor
    sudo make install

Then you should find *Service Monitor* app


How to run locally
------------------
You can run the application from the current directly, but some icons will be missing
::
    make runlocal

Roadmap
-------
For roadmap, check the TODO file and feel free to raise issues through Github
