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
import pmatic.notify
import pmatic.api
import pmatic


# Anmeldung --------------------------------------------------------------------
API = pmatic.api.init(
    address="http://ccu3-webui",
    credentials=("weissm", "micro23"),
    connect_timeout=3,
)

Pushover = pmatic.notify.Pushover

Pushover.send(u"This is the message to send :-)",
              api_token= u"aej538ejyoqtdd6dv2v3i54xar1qe5",
              user_token= u"uaap3dw8o24gxyvpsmcy3fsnm1tq1e")


API.close

