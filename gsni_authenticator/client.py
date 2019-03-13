#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    TCACACS Authentication client - System Tray
    @copyright: (c) Copyright BMI Corp. 2013-2016 All Rights Reserved
    @author:    João Pinto <joao.pinto@pt.BMI.com>
"""
import pygtk

pygtk.require("2.0")

import gtk
import gobject
import resources
import dbus
import pynotify
import gnomekeyring
import os
from socket import AF_INET
from os.path import isfile
from dbus.mainloop.glib import DBusGMainLoop
from configobj import ConfigObj
from gettext import gettext as _
from xdg.BaseDirectory import xdg_config_home
from os.path import join, exists
from threading import Thread
from tacacs import Auth
from watcher import AGNClientConnectWatcher
from keyring import Keyring
from entrydialog import EntryDialog
from getnifs import get_network_interfaces

pynotify.init("gsni-authenticator")

class AuthClient(object):
    def __init__(self, options):
        self.options = options
        self.debuglevel = 1 if options.debug else 0
        self.is_manual_auth = False
        self.server = self.password = self.username = None
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.dbus_get_network_manager().connect_to_signal("StateChanged", self.onNetworkStateChanged)
        self.dbus_get_network_manager_settings().connect_to_signal("NewConnection", self.onNewConnection)
        self.tray = gtk.StatusIcon()
        self.set_icon('gsni_auth_regular.png')
        self.tray.set_tooltip(_('Not authenticated'))
        self.tray.connect('popup-menu', self.on_right_click, 'test')
        self.doing_login = False
        self.settings_dialog = False
        config_dir = options.config_dir or join(xdg_config_home, 'gsni-authenticator')
        if options.is_spain:        
            resources.UI_DIR_NAME = 'ui_es'
        else:
            resources.UI_DIR_NAME = 'ui_pt'
        if options.set_icon_flag:
            resources.UI_DIR_NAME = 'ui_'+options.set_icon_flag
        print config_dir
        if not exists(config_dir):
            os.makedirs(config_dir)

        self.settings_fname = join(config_dir, 'auth.conf')

        self.agnclient_watcher = AGNClientConnectWatcher(self.on_agnclient_connect)
        self.agnclient_watcher.start()

    def on_right_click(self, icon, event_button, event_time, data=None):
        self.make_menu(event_button, event_time, data)

    def make_menu(self, event_button, event_time, data):
        menu = gtk.Menu()

        # show data string
        item = gtk.MenuItem("Authenticate")
        if not self.doing_login:
            item.show()

        menu.append(item)
        item.connect('activate', self.do_manual_auth)

        # show settings dialog
        item = gtk.MenuItem("Config...")
        if self.settings_dialog:
            item.set_sensitive(False)
        item.show()
        menu.append(item)
        item.connect('activate', self.do_config)

        # show about dialog
        item = gtk.MenuItem("About")
        item.show()
        menu.append(item)
        item.connect('activate', self.show_about_dialog)

        separator = gtk.SeparatorMenuItem()
        separator.show()
        menu.append(separator)
        # add quit item
        quit = gtk.MenuItem("Quit")
        quit.show()
        menu.append(quit)

        quit.connect('activate', gtk.main_quit)

        menu.popup(None, None, gtk.status_icon_position_menu,
                   event_button, event_time, self.tray)

    def _check_config(self):
        if not exists(self.settings_fname):
            config = ConfigObj()
            config.filename = self.settings_fname
            self.server = config['server'] = '158.98.137.17:950'
            self.username = config['user'] = 'your_gsni_username'
            self.password = None
            config.write()
        else:
            config = ConfigObj(self.settings_fname)
            self.server = config['server']
            self.username = config['user']

        self.keyring = Keyring('gsni-authenticator', self.username, self.server, 'gsni')

        # Support < 0.3 passwords stored on file
        if 'pass' in config:
            self.password = config['pass']
            del config['pass']
            self.keyring.set_password(self.password)
            config.write()
        if not self.password:
            try:
                self.password = self.keyring.get_password()
            except gnomekeyring.NoMatchError:
                return False
        return True

    def do_manual_auth(self, widget):
        self.is_manual_auth = True
        self.do_login(widget)

    def do_login(self, widget):
        if not self._check_config():
            if self.is_manual_auth and not self._run_config():
                return
        if self.doing_login:
            return
        self.doing_login = True
        self._login_in_thread()

    def on_agnclient_connect(self):
        self.do_login(self)

    def do_config(self, widget):
        self._check_config()
        self._run_config()

    def _run_config(self):
        prompt = EntryDialog(default_value=self.server, buttons=gtk.BUTTONS_OK_CANCEL)
        prompt.set_markup('What is your GSNI server?')
        server = prompt.run()
        prompt.hide()
        if not server:
            return False
        prompt = EntryDialog(default_value=self.username, buttons=gtk.BUTTONS_OK_CANCEL)
        prompt.set_markup('What is your GSNI username?')
        username = prompt.run()
        prompt.hide()
        if not username:
            return False
        prompt = EntryDialog(default_value=self.password or ''
                             , buttons=gtk.BUTTONS_OK_CANCEL
                             , visibility=False)
        prompt.set_markup('What is your GSNI password?')
        password = prompt.run()
        prompt.hide()
        if not password:
            return False
        self.password = password
        self.keyring.set_password(self.password)
        config = ConfigObj(self.settings_fname)
        config['server'] = self.server = server
        config['user'] = self.username = username
        config.write()
        return True

    def _login_in_thread(self):
        gobject.timeout_add(300, self.swap_icon, True)
        Thread(target=self._login_function).start()

    def _login_function(self):
        tacacs = Auth("https://" + self.server, self.debuglevel, self.options.three_steps_auth)
        login_result = tacacs.login(self.username, self.password)
        gobject.idle_add(self._login_completed, login_result)

    def _login_completed(self, ret):
        self.doing_login = False
        print "Ret=", ret

        if ret == -1:
            retry_login = 600  # Retry in 10mins
            self.set_icon('gsni_auth_regular.png')
            self.tray.set_tooltip('Unable to connect to server ' + self.server)
        elif ret == -2:
            retry_login = None
            self.set_icon('gsni_auth_error.png')
            self.tray.set_tooltip('Failed authentication on ' + self.server)
        elif ret == 0:
            retry_login = 3600  # Retry in 1h
            self.set_icon('gsni_auth_connected.png')
            self.tray.set_tooltip('Successfully authenticated to ' + self.server)

        if retry_login:
            print "Repeating authentication in %d minutes." % int(retry_login / 60)
            gobject.timeout_add_seconds(retry_login, self.do_login, None)
        self.is_manual_auth = False

    def dbus_get_network_manager(self):
        """Gets the network manager dbus interface."""
        print "Getting NetworkManager DBUS interfacse"
        proxy = self.bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        return dbus.Interface(proxy, 'org.freedesktop.NetworkManager')

    def dbus_get_network_manager_settings(self):
        """Gets the network manager dbus interface."""
        print "Getting NetworkManager(VP) DBUS interfacse"
        proxy = self.bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager/Settings')
        return dbus.Interface(proxy, 'org.freedesktop.NetworkManager.Settings')
        

    def onNetworkStateChanged(self, state):
        print "Network state changed to", state
        if state == 70 :
            print "Checking for an BMI IP address"
            if self.running_with_ibm_network():
                print "Network connection established and running with BMI net, authenticating... "
                self.on_agnclient_connect()

    def onNewConnection(self, state):
        print "New connection detected"
        print "Checking for an BMI IP address"
        if self.running_with_ibm_network():
            print "Network connection established and running with BMI net, authenticating... "
            self.on_agnclient_connect()

                

    def swap_icon(self, value):
        if not self.doing_login:
            return
        if value:
            self.set_icon('gsni_auth_connected.png')
        else:
            self.set_icon('gsni_auth_regular.png')
        gobject.timeout_add(300, self.swap_icon, value ^ True)

    def running_with_ibm_network(self):
        for network in get_network_interfaces():
            addresses = network.addresses.get(AF_INET)
            if not addresses:
                continue
            for addr in addresses:
                if addr.startswith('9.'):
                    return True
            continue
        return False

    def run(self):
        gtk.gdk.threads_init()
        if self.running_with_ibm_network():
            gobject.idle_add(self.do_login, None)
        gtk.main()

    def set_icon(self, name):
        self.tray.set_from_file(resources.get_ui_asset(name))
        self.Icon_name = name

    def show_about_dialog(self, widget):
        about_dialog = gtk.AboutDialog()
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_icon_name("gsni-authenticator")
        about_dialog.set_name('GSNI Authenticator')
        about_dialog.set_version('0.8.4')
        about_dialog.set_copyright("(C) 2013-2018 BMI")
        about_dialog.set_comments(_("Automated authentication with a gSNI server"))
        about_dialog.set_authors(['joao.pinto@pt.BMI.com'])
        about_dialog.run()
        about_dialog.destroy()

    def desktop_notify(self, status_change, icon_path):
        notify = pynotify.Notification("GSNI Authentication",
                                       status_change,
                                       icon_path
        )
        notify.set_urgency(pynotify.URGENCY_LOW)
        notify.set_timeout(3000)
        notify.show()
