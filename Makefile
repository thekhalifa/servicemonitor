# SPDX-License-Identifier: GPL-3.0-or-later

prefix=/usr
DATA_DIR=data/
SRC_DIR=src/
TEST_DIR=tests/
DIST_DIR=dist/
TARBALL_BASE=servicemonitor-0.2

APP_ICON_DIR=${DATA_DIR}icons/apps64/
STATUS_ICON_DIR=${DATA_DIR}icons/status48/
DESKTOP_FILE=com.github.thekhalifa.servicemonitor.desktop
SCHEMA_FILE=com.github.thekhalifa.servicemonitor.gschema.xml
POLKIT_FILE=com.github.thekhalifa.servicemonitor.policy
RUN_FILE=servicemonitor

TARGET_INSTALL_DIR=${DESTDIR}${prefix}/lib/servicemonitor/
TARGET_ICON_DIR=${DESTDIR}${prefix}/share/icons/hicolor/
TARGET_APP_ICON_DIR=${TARGET_ICON_DIR}64x64/apps/
TARGET_STATUS_ICON_DIR=${TARGET_ICON_DIR}48x48/status/
TARGET_SCHEMA_DIR=${DESTDIR}${prefix}/share/glib-2.0/schemas/
TARGET_POLKIT_DIR=${DESTDIR}${prefix}/share/polkit-1/actions/
TARGET_DESKTOP_DIR=${DESTDIR}${prefix}/share/applications/
TARGET_BIN_DIR=${DESTDIR}${prefix}/bin/


help:
	@echo "Please specify a target"
	@echo "  -- clean"
	@echo "  -- dist (creates a dist tarball)"
	@echo "  -- manual-install (to install it system wide) [requires super user privileges]"
	@echo "  -- manual-uninstall (to remove system installed files) [requires super user privileges]"
	@echo "  -- install (for packaging that takes care of post install, otherwise use 'manualinstall')"


clean:
	@echo Removing dist dir and pycache files
	@rm -rfv src/__pycache__
	@rm -rfv ${DIST_DIR}
	@rm -fv ${TARBALL_BASE}.tar.gz

dist: clean
	mkdir -pv ${DIST_DIR}
	cp -rv ${DATA_DIR} ${SRC_DIR} ${TEST_DIR} ${DIST_DIR}
	cp -v ${RUN_FILE} LICENSE README.rst Makefile ${DIST_DIR}
	tar -czf ${TARBALL_BASE}.tar.gz dist/ --transform "s;dist;${TARBALL_BASE};g"

.PHONY: dist

test:
	PYTHONPATH=. /usr/bin/python3 tests/test_unit.py
	# these tests require closing several ui dialogs that popup, needs a human
	# cd tests && PYTHONPATH=.. python3 test_application.py
	# These tests need to be run on a live dbus/systemd host
	# PYTHONPATH=. /usr/bin/python3 tests/test_dbuscaller.py

install: installpackage
	@echo Install complete

manual-install: installpackage installconfig
	@echo Install complete

installpackage:
	install -vdm 755 ${TARGET_INSTALL_DIR}
	install -vm 644 ${SRC_DIR}*.py ${TARGET_INSTALL_DIR}
	chmod 0755 ${TARGET_INSTALL_DIR}unithelper.py
	install -vm 644 ${SRC_DIR}*.ui ${TARGET_INSTALL_DIR}
	install -vm 755 ${RUN_FILE} ${TARGET_BIN_DIR}
	@# schema
	install -vm 644 ${DATA_DIR}${SCHEMA_FILE} ${TARGET_SCHEMA_DIR}
	@# icons
	install -vdm 644 ${TARGET_STATUS_ICON_DIR}
	install -vdm 644 ${TARGET_APP_ICON_DIR}
	install -vm 644 ${STATUS_ICON_DIR}* ${TARGET_STATUS_ICON_DIR}
	install -vm 644 ${APP_ICON_DIR}* ${TARGET_APP_ICON_DIR}
	@# polkit
	install -vm 644 ${DATA_DIR}${POLKIT_FILE} ${TARGET_POLKIT_DIR}
	@# desktop
	install -vm 644 ${DATA_DIR}${DESKTOP_FILE} ${TARGET_DESKTOP_DIR}

installconfig:
	@# schema
	glib-compile-schemas ${TARGET_SCHEMA_DIR}
	@# icons
	gtk-update-icon-cache ${TARGET_ICON_DIR}
	@# desktop
	xdg-desktop-menu install --novendor ${TARGET_DESKTOP_DIR}${DESKTOP_FILE}


manual-uninstall:
	@# desktop
	xdg-desktop-menu uninstall --novendor ${DESKTOP_FILE}
	rm -fv ${TARGET_DESKTOP_DIR}${DESKTOP_FILE}
	@# polkit
	rm -fv ${TARGET_POLKIT_DIR}${POLKIT_FILE}
	@# icons - leave icons
	@# schema
	rm -fv  ${TARGET_SCHEMA_DIR}${SCHEMA_FILE}
	glib-compile-schemas ${TARGET_SCHEMA_DIR}
	@# package
	rm -fv ${TARGET_BIN_DIR}${RUN_FILE}
	rm -rfv ${TARGET_INSTALL_DIR}
