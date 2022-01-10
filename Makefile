# SPDX-License-Identifier: GPL-3.0-or-later
DATA_DIR=data/
SRC_DIR=src/
UI_DIR=${DATA_DIR}ui/
APP_ICON_DIR=${DATA_DIR}icons/apps/
STATUS_ICON_DIR=${DATA_DIR}icons/status/
DESKTOP_FILE=${DATA_DIR}com.github.thekhalifa.servicemonitor.desktop
SCHEMA_FILE=${DATA_DIR}com.github.thekhalifa.servicemonitor.gschema.xml
POLKIT_FILE=${DATA_DIR}com.github.thekhalifa.servicemonitor.policy
RUN_FILE=servicemonitor

TARGET_INSTALL_DIR=/usr/lib/servicemonitor/
TARGET_ICON_DIR=/usr/share/icons/hicolor/
TARGET_APP_ICON_DIR=${TARGET_ICON_DIR}scalable/apps/
TARGET_STATUS_ICON_DIR=${TARGET_ICON_DIR}scalable/status/
TARGET_SCHEMA_DIR=/usr/share/glib-2.0/schemas
TARGET_POLKIT_DIR=/usr/share/polkit-1/actions
TARGET_DESKTOP_DIR=/usr/share/applications
TARGET_BIN_DIR=/usr/bin/

.DEFAULT_GOAL := usage

usage:
	@echo "Please specify a target"
	@echo "  -- runlocal (to run in current directory)"
	@echo "  -- install (to install it system wide)"

runlocal:
	python3 src/application.py data/ui

install: installpackage installschema installicons installpolkit installdesktop
	@echo Install complete

installschema:
	install -vm 644 ${SCHEMA_FILE} ${TARGET_SCHEMA_DIR}
	glib-compile-schemas ${TARGET_SCHEMA_DIR}

installicons:
	install -vm 644 ${STATUS_ICON_DIR}* ${TARGET_STATUS_ICON_DIR}
	install -vm 644 ${APP_ICON_DIR}* ${TARGET_APP_ICON_DIR}
	gtk-update-icon-cache ${TARGET_ICON_DIR}

installpolkit:
	install -vm 644 ${POLKIT_FILE} ${TARGET_POLKIT_DIR}

installdesktop:
	install -vm 644 ${DESKTOP_FILE} ${TARGET_DESKTOP_DIR}
	xdg-desktop-menu install --novendor ${DESKTOP_FILE}

installpackage:
	install -vdm 755 ${TARGET_INSTALL_DIR}
	install -vm 755 ${SRC_DIR}*.py ${TARGET_INSTALL_DIR}
	install -vm 644 ${UI_DIR}*.ui ${TARGET_INSTALL_DIR}
	install -vm 755 ${RUN_FILE} ${TARGET_BIN_DIR}
