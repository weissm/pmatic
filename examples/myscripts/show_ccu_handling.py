#!/usr/bin/env python
# encoding: utf-8
#
# Beispiele, die allerdings ohne die entsprechenden Geräte/Variablen nicht funktionieren!
# ohne Gewähr für Richtigkeit etc.
# (angepasst auf die Standard pmatic - Bibliothek)
#


from __future__ import print_function

import sys
sys.path.append("pmatic/module_py")
sys.path.append("c:\\Users\\mweiss\\source\\repos\\pmatic\\")
print(sys.path)
#import pmatic.notify
#import pmatic.manager
import pmatic.api
#import pmatic.xml_api
import pmatic


# Anmeldung --------------------------------------------------------------------
# user=sys.argv[1]
# password=sys.argv[2]

user="PmaticAdmin"
password="EPIC-SECRET-PW"

ccu = pmatic.CCU(
    address="http://ccu3-webui",
    credentials=(user, password)
    )
API = pmatic.api.init(
    address="http://ccu3-webui",
    credentials=(user, password),
#    credentials=pmatic.manager.Config.ccu_credentials,
    connect_timeout=3,
)


devices = ccu.devices
print ("#devices: ", len(devices))
print(devices)

#for device in ccu.devices.query(device_type="HM-RCV-50"):
#    test = device.summary_state

for device in ccu.devices:
    print("%-20s %s %s %s" % (device.name, device.type, device.address, device.version))
uu
for room in ccu.rooms:
    print(room.name)
    for device in room.devices:
       print("  %s: %s" % (device.name, device.summary_state))

ccu.close()
exit(0)

