# SPDX-License-Identifier: GPL-3.0-or-later
DATA_DIR=data/
SRC_DIR=src/
APP_ICON_DIR=${DATA_DIR}icons/apps/
STATUS_ICON_DIR=${DATA_DIR}icons/status/
DESKTOP_FILE=com.github.thekhalifa.servicemonitor.desktop
SCHEMA_FILE=com.github.thekhalifa.servicemonitor.gschema.xml
POLKIT_FILE=com.github.thekhalifa.servicemonitor.policy
RUN_FILE=servicemonitor

TARGET_INSTALL_DIR=/usr/lib/servicemonitor/
TARGET_ICON_DIR=/usr/share/icons/hicolor/
TARGET_APP_ICON_DIR=${TARGET_ICON_DIR}48x48/apps/
TARGET_STATUS_ICON_DIR=${TARGET_ICON_DIR}scalable/status/
TARGET_SCHEMA_DIR=/usr/share/glib-2.0/schemas/
TARGET_POLKIT_DIR=/usr/share/polkit-1/actions/
TARGET_DESKTOP_DIR=/usr/share/applications/
TARGET_BIN_DIR=/usr/bin/

.DEFAULT_GOAL := usage

usage:
	@echo "Please specify a target"
	@echo "  -- install (to install it system wide) [requires super user privileges]"
	@echo "  -- uninstall (to remove system installed files) [requires super user privileges]"

install: installpackage installdata
	@echo Install complete

installdata:
	@# schema
	install -vm 644 ${DATA_DIR}${SCHEMA_FILE} ${TARGET_SCHEMA_DIR}
	glib-compile-schemas ${TARGET_SCHEMA_DIR}
	@# icons
	install -vm 644 ${STATUS_ICON_DIR}* ${TARGET_STATUS_ICON_DIR}
	install -vm 644 ${APP_ICON_DIR}* ${TARGET_APP_ICON_DIR}
	gtk-update-icon-cache ${TARGET_ICON_DIR}
	@# polkit
	install -vm 644 ${DATA_DIR}${POLKIT_FILE} ${TARGET_POLKIT_DIR}
	@# desktop
	install -vm 644 ${DATA_DIR}${DESKTOP_FILE} ${TARGET_DESKTOP_DIR}
	xdg-desktop-menu install --novendor ${TARGET_DESKTOP_DIR}${DESKTOP_FILE}

installpackage:
	install -vdm 755 ${TARGET_INSTALL_DIR}
	install -vm 644 ${SRC_DIR}*.py ${TARGET_INSTALL_DIR}
	chmod 0755 ${TARGET_INSTALL_DIR}application.py ${TARGET_INSTALL_DIR}unithelper.py
	install -vm 644 ${SRC_DIR}*.ui ${TARGET_INSTALL_DIR}
	install -vm 755 ${RUN_FILE} ${TARGET_BIN_DIR}

uninstall:
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

