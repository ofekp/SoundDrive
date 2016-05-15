#!/usr/bin/python2.7

# sudo apt-get install bluez
# sudo apt-get install python-bluez
import bluetooth

print "Performing BT inquery"

nearby_devices = bluetooth.discover_devices(lookup_names = True)

print "found %d devices" % len(nearby_devices)

for addr, name in nearby_devices:
    print "    %s - %s" % (addr, name)


# Implementing a BT client

BT_MAC = "00:1A:7D:DA:71:13"
port = 1

sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((addr, port))

#sock.send("hello!")

sock.close()


# Refer to: "https://wiki.archlinux.org/index.php/Bluetooth_headset#Headset_via_Bluez5.2FPulseAudio"
# sudo apt-get install pulseaudio pulseaudio-module-bluetooth
# pactl load-module module-bluetooth-discover
# sudo echo "pactl load-module module-bluetooth-discover" >> /etc/pulse/default.pa
# sudo apt-get install pavucontrol


