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

user="weissm"
password="micro23"

API = pmatic.api.init(
    address="http://ccu3-webui",
    credentials=(user, password),
#    credentials=pmatic.manager.Config.ccu_credentials,
    connect_timeout=3,
)

# Methoden auflisten ---------------------------------------------------------
# API.print_methods()

# Devices auflisten ------------------------------------------------------------
try:
  devices = API.device_list_all_detail()
except:
  pass
  devices = API.device_list_all()

print (len(devices))

line_fmt = "%-30s %s %s"

# Print the header
print(line_fmt % ("Name", "type", "address"))
print(line_fmt % ("-" * 30, "-" * 6, "-" * 6))

# Loop all devices, only care about shutter contacts
for device in devices:
    print (device["name"], device["type"], device["address"])
    address = device["address"]
    interface = device["interface"]
    try:
      print (API.interface_get_paramset(address=address, interface=interface, paramsetKey="MASTER"))
      print (API.interface_get_paramset(address=address, interface=interface, paramsetKey="VALUES"))
      paraset = API.interface_get_paramset(address=address, interface=interface, paramsetKey="MASTER")
      if len(paraset)>0 :
        print("get parmaeter: ", paraset)
      else:
        print("EMTPY get parmaeter: " )
    except Exception as e:
      print(e)
    try:
      test = API.interface_get_value(address=address, interface=interface, valueKey='UNREACH')
      print(test)
    except Exception as e:
      print(e)
#    for c in device["channels"]:
#        print (c)

exit(0)

# Devices auflisten Ende -------------------------------------------------------

try:
	rooms = API.room_get_all()
except:
  pass

line_fmt = "%-30s %-30s %-30s %-30s"
for room in rooms:
    print ("----------------------------------------------------------------------------------------------------------------------------------")
    print (room["name"], room["description"], room["channelIds"])
    print(room)
    print(line_fmt % ("name", "type", "address", "interface"))
    print(line_fmt % ("-" * 30, "-" * 6, "-" * 6, "-" * 6))
    for c in room["channelIds"]:
      device = API.device_get(id=c)
      print(line_fmt % (device["name"],device["type"],device["address"],device["interface"]))

print("done")

# Systemvariable auslesen/Setzen ------------------------------------------------------
try:
  print ("[Anwesenheit]: ", API.sys_var_get_value_by_name(name="[Anwesenheit]"))
#  API.sys_var_set_bool(name="svb_Test_sv", value="0")
except Exception as err:
  print ("svb_Test_sv_Fehler:", Exception, err)
# Achtung, zum Setzen bei anderem Datentyp anderer Aufruf!


# Anzahl Servicemeldungen ------------------------------------------------------
try:
  svc_anz = API.interface_get_service_message_count(interface="BidCos-RF")
  print ("Svc_Anz:", svc_anz)
except Exception as err:
  print ("Svc_Anz_Fehler:", Exception, err)


# Rollladen/Markise (Typ: HM-LC-Bl1PBU-FM, SN: <SN>, Name: Rollladen)------
try:
  rollostand = float(API.channel_get_value(id="Rollladen:1"))
  print ("Rollladen: ",rollostand)
  Ergebnis=API.interface_set_value(interface="BidCos-RF", address="<SN>:1", valueKey="LEVEL", type="string", value="1.0")
except Exception as err:
  print ("Rollladen_Fehler:", Exception, err)


# Lampe (Typ: HM-LC-Sw1-Pl-DN-R1, SN: <SN>, Name=Lampe) ------------------------
try:
  lampe_anaus = API.channel_get_value(id="Lampe:1")
  print ("Lampe: ",lampe_anaus)
  Ergebnis=API.interface_set_value(interface="BidCos-RF", address="<SN>:1", valueKey="STATE", type="bool", value="true")
except Exception as err:
  print ("Lampe_Fehler:", Exception, err)


API.close

