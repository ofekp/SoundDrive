#!/usr/bin/python2.7

import dbus
import gobject
from dbus.mainloop.glib import DBusGMainLoop
import subprocess

# MAC address of the bluetooth device
DEV_MAC = '00:1A:7D:DA:71:13'

dbus_loop = DBusGMainLoop()
bus = dbus.SystemBus(mainloop=dbus_loop)

man = bus.get_object('org.bluez', '/')
print man
iface = dbus.Interface(man, 'org.bluez.Manager')
adapterPath = iface.DefaultAdapter()

outdevice = bus.get_object('org.bluez', adapterPath + "/dev_" + DEV_MAC)

def cb(iface=None, mbr=None, path=None):
    if ("org.bluez.Headset" == iface and path.find(DEV_MAC) > -1):
        print 'iface: %s' % iface
        print 'mbr: %s' % mbr
        print 'path: %s' % path
        print "\n"
        print "matched"

        if mbr == "Connected":
            print "Connected :)"
        elif mbr == "Disconnected":
            print "Disconnected :("

outdevice.connect_to_signal("Connected", cd, interface_keyword="iface", member_keyword="mbr", path_keyword="path")
outdevice.connect_to_signal("Disconnected", cd, interface_keyword="iface", member_keyword="mbr", path_keyword="path")

loop = gobject.MainLoop()
loop.run()

            
