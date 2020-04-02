#!/usr/bin/python
import pmatic
ccu = pmatic.CCU(address="http://ccu3-webui", credentials=("weissm", "micro23"))

print("Low battery: ")
print(len(ccu.CCUDevices))
for device in ccu.CCUDevices:
    print("  %s" % device.name)
