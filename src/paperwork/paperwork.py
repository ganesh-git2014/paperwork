#!/usr/bin/env python3
#    Paperwork - Using OCR to grep dead trees the easy way
#    Copyright (C) 2012-2014  Jerome Flesch
#
#    Paperwork is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Paperwork is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Paperwork.  If not, see <http://www.gnu.org/licenses/>.
"""
Bootstrapping code
"""

import os
import sys

import gettext
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Poppler', '0.18')
gi.require_version('PangoCairo', '1.0')

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import GLib
import locale
import logging
import signal

import pyinsane2

from .frontend.mainwindow import ActionRefreshIndex, MainWindow
from .frontend.util.config import load_config

logger = logging.getLogger(__name__)


LOCALE_PATHS = []
if getattr(sys, 'frozen', False):
    LOCALE_PATHS += [os.path.join(sys._MEIPASS, "data")]
LOCALE_PATHS += [
    ('.'),
    ('/usr/local/share/'),
    ('/usr/share/'),
]

def init_logging():
    formatter = logging.Formatter(
        '%(levelname)-6s %(name)-30s %(message)s')
    handler = logging.StreamHandler()
    logger = logging.getLogger()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel({
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }[os.getenv("PAPERWORK_VERBOSE", "INFO")])


def set_locale():
    """
    Enable locale support
    """
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        # happens e.g. when LC_ALL is set to a nonexisting locale
        logger.warning("Failed to set LC_ALL, disabling localization")
        return

    got_locales = False
    locales_path = None

    for locale_base in LOCALE_PATHS:
        locales_path = os.path.join(locale_base, "locale")
        logger.debug("Looking for locales in '%s' ..." % locales_path)
        mo_file = gettext.find("paperwork", locales_path)
        if mo_file is None:
            # No paperwork.mo found, try next path
            continue
        if not os.access(mo_file, os.R_OK):
            logger.debug("No read permission for locale '%s'" % locales_path)
            continue
        got_locales = True
        break

    if not got_locales:
        logger.warning("No suitable localization file found.")
    else:
        logger.info("Using locales in '%s'" % locales_path)
        for module in (gettext, locale):
            module.bindtextdomain('paperwork', locales_path)
            module.textdomain('paperwork')


def main():
    """
    Where everything start.
    """
    init_logging()
    set_locale()

    GObject.threads_init()

    if hasattr(GLib, "unix_signal_add"):
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT,
                             Gtk.main_quit, None)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM,
                             Gtk.main_quit, None)

    try:
        pyinsane2.init()

        config = load_config()
        config.read()

        main_win = MainWindow(config)
        ActionRefreshIndex(main_win, config).do()
        Gtk.main()

        for scheduler in main_win.schedulers.values():
            scheduler.stop()

        config.write()
    finally:
        logger.info("Good bye")


if __name__ == "__main__":
    main()
