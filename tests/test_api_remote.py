#!/usr/bin/env python
# encoding: utf-8
#
# pmatic - Python API for Homematic. Easy to use.
# Copyright (C) 2016 Lars Michelsen <lm@larsmichelsen.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Add Python 3.x behaviour to 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytest

import pmatic.utils as utils
import pmatic.api
from pmatic.exceptions import PMException

import lib


# FIXME: This must be moved to a general place. When there are tests in other
# test_*.py modules which are recording data, this might delete the files of
# the other modules when they have been executed before test_api_remote.py.
#import os
#import glob
#def setup_module():
#    """ When executed against a real CCU (recording mode), all existing
#    resource files are deleted."""
#    if lib.is_testing_with_real_ccu():
#        for f in glob.glob("tests/resources/*.data") \
#               + glob.glob("tests/resources/*.status") \
#               + glob.glob("tests/resources/*.response"):
#            # Don't delete the pushover test files when testing with real CCU
#            if "/urlopen_" not in f:
#                os.unlink(f)


def test_init_address_invalid():
    with pytest.raises(PMException) as e:
        pmatic.api.RemoteAPI(address=None, credentials=("", ""))
    assert "address of the CCU" in str(e)


def test_init_address_missing_proto(monkeypatch):
    # Disable API calls of constructor
    monkeypatch.setattr(pmatic.api.RemoteAPI, '_login', lambda x: None)
    monkeypatch.setattr(pmatic.api.RemoteAPI, '_init_methods', lambda x: None)

    api = pmatic.api.RemoteAPI(address="127.0.0.1", credentials=("", ""))
    assert api.address == "http://127.0.0.1"


def test_init_credentials_invalid(monkeypatch):
    # Disable API calls of constructor
    monkeypatch.setattr(pmatic.api.RemoteAPI, '_login', lambda x: None)
    monkeypatch.setattr(pmatic.api.RemoteAPI, '_init_methods', lambda x: None)

    with pytest.raises(PMException) as e:
        pmatic.api.RemoteAPI(address="http://127.0.0.1", credentials=None)
    assert "Please specify" in str(e)

    with pytest.raises(PMException) as e:
        pmatic.api.RemoteAPI(address="http://127.0.0.1", credentials=("", "", ""))
    assert "two elements" in str(e)

    with pytest.raises(PMException) as e:
        pmatic.api.RemoteAPI(address="http://127.0.0.1", credentials=("",))
    assert "two elements" in str(e)

    with pytest.raises(PMException) as e:
        pmatic.api.RemoteAPI(address="http://127.0.0.1", credentials=(None, None))
    assert "username" in str(e)

    with pytest.raises(PMException) as e:
        pmatic.api.RemoteAPI(address="http://127.0.0.1", credentials=("", None))
    assert "password" in str(e)


def test_init_timeout_invalid(monkeypatch):
    # Disable API calls of constructor
    monkeypatch.setattr(pmatic.api.RemoteAPI, '_login', lambda x: None)
    monkeypatch.setattr(pmatic.api.RemoteAPI, '_init_methods', lambda x: None)

    with pytest.raises(PMException) as e:
        pmatic.api.RemoteAPI(address="http://127.0.0.1", credentials=("", ""),
                             connect_timeout=None)
    assert "Invalid timeout value" in str(e)


class TestRemoteAPILowLevel(lib.TestRemoteAPI):
    def test_address(self, API):
        assert API.address == API._address


    def test_logged_in(self, API):
        assert API._session_id is None

        # Making an API call is lazy initializing the session
        devices = API.device_list_all_detail()
        assert len(devices) > 10

        assert len(API._session_id) == 10


    def test_double_login(self, API):
        assert len(API._session_id) == 10
        with pytest.raises(PMException) as e:
            API._login()
        assert "Already logged in" in str(e)


    def test_methods_initialized(self, API):
        assert len(API._methods) > 10
        for method in API._methods.values():
            assert "INFO" in method
            assert "NAME" in method
            assert "LEVEL" in method
            assert "ARGUMENTS" in method
            assert "INT_ARGUMENTS" in method
            assert "SCRIPT_FILE" in method


    def test_print_methods(self, API, capsys):
        API.print_methods()
        out, err = capsys.readouterr()
        assert "API.ccu_get_serial()" in out
        assert "API.user_set_language" in out
        assert err == ""


    def test_device_list_all_detail(self, API):
        devices = API.device_list_all_detail()
        assert len(devices) > 10
        for device in devices:
            assert "id" in device
            assert "name" in device
            assert "channels" in device
            assert len(device["channels"]) > 0


    def test_room_list_all(self, API):
        for room_id in API.room_list_all():
            assert utils.is_text(room_id)


    def test_room_get(self, API):
        first_room_id = API.room_list_all()[0]
        room = API.room_get(id=first_room_id)
        assert "name" in room
        assert "description" in room
        assert "channelIds" in room
        assert isinstance(room["channelIds"], list)


    def test_room_get_all(self, API):
        for room in API.room_get_all():
            assert utils.is_text(room["name"])
            room["name"].encode("utf-8")
            assert utils.is_text(room["description"])
            room["description"].encode("utf-8")
            assert isinstance(room["channelIds"], list)


    def test_ccu_get_ssh_state(self, API):
        assert API.ccu_get_ssh_state() == 1


    def test_ccu_get_serial(self, API):
        serial = API.ccu_get_serial()
        assert utils.is_text(serial)
        assert len(serial) == 10
        assert serial.startswith("QEQ")

    def test_ccu_get_serial_ccu2(self, APICCU2):
        serial = APICCU2.ccu_get_serial()
        assert utils.is_text(serial)
        assert len(serial) == 10
        assert serial.startswith("KEQ")

    def test_interface_list_interfaces(self, API):
        interfaces = API.interface_list_interfaces()
        assert len(interfaces) > 0
        for interface in interfaces:
            assert utils.is_text(interface["info"])
            assert utils.is_text(interface["name"])
            assert isinstance(interface["port"], int)



# FIXME: Write tests for untested methods.
#API.bidcos__wired_get_configuration_wired()
#  Liefert die aktuelle Konfiguration des BidCoS-Wired Dienstes
#API.bidcos__wired_set_configuration_wired(interfaces)
#  Setzt die Konfiguration des BidCoS-Wired Dienstes
#API.bidcos_change_lan_gateway_key(lgwclass, lgwserial, lgwip, newkey, curkey)
#  Bereitet das Setzen eines LAN Gateway Schlüssels vor.
#API.bidcos_rf_create_key_file(key)
#  Generiert die Datei /etc/config/keys
#API.bidcos_rf_get_configuration_rf()
#  Liefert die aktuelle Konfiguration des BidCoS-RF Dienstes
#API.bidcos_rf_is_key_set()
#  Ermittelt, ob ein Systemsicherheitsschlüssel im ARM7 gesetzt ist
#API.bidcos_rf_set_configuration_rf(interfaces)
#  Setzt die Konfiguration des BidCoS-RF Dienstes
#API.bidcos_rf_validate_key(key)
#  Prüft, ob der angegebe Schlüssel dem System-Sicherheitsschlüssel entspricht
#API.ccu_get_version()
#  Liefert die Firmware-Version der HomeMatic Zentrale
#API.ccu_restart_ssh_daemon()
#  Restartet den SSH-Daemon
#API.ccu_set_ssh(mode)
#  Aktiviert oder. deaktiviert den SSH-Zugang der HomeMatic Zentrale
#API.ccu_set_ssh_password(passwd)
#  Setzt das Passwort für den SSH-Zugang
#API.channel_get_name(address)
#  Liefert den Namen des Kanals
#API.channel_get_value(id)
#  Liefert den Wert des Kanals
#API.channel_list_program_ids(id)
#  Liefert die Ids aller Programme, in denen der Kanal verwendet wird
#API.channel_poll_com_test(id, testId)
#  Fragt das Ergebnis eines laufenden Funktionstests ab
#API.channel_set_logging(id, isLogged)
#  Aktiviert bzw. deaktiviert die Protokollierung des Kanals
#API.channel_set_mode(id)
#  Legt den Übertragungs-Modus (Standard oder Gesichert (AES)) des Kanals fest
#API.channel_set_name(id)
#  Legt den Namen des Kanals fest
#API.channel_set_usability(id, isUsable)
#  Legt fest, ob der Kanal für normale Anwender bedienbar
#API.channel_set_visibility(id, isVisible)
#  Legt fest, ob der Kanal für normale Anwender sichtbar ist
#API.channel_start_com_test(id)
#  Startet den Funktionstest für den Kanal
#API.device_get(id)
#  Liefert Detailinformationen zu einem Gerät
#API.device_getrega_id_by_address(address)
#  Ermittelt die ReGa-ID eines Gerätes aufgrund der Seriennummer
#API.device_has_links_or_programs(id)
#  Ermittelt, ob das Geräte in direkten Verknüpfungen oder Programmen verwendet wird
#API.device_list_all()
#  Liefert die Ids aller fertig konfigurierten Geräte
#API.device_list_program_ids(id)
#  Liefert die Ids aller Programme, die mindestens einen Kanal des Geräts verwenden
#API.device_poll_com_test(id, testId)
#  Prüft, ob Ergebnisse für einen Funktionstest vorliegen
#API.device_set_name(id, name)
#  Legt den Namen des Geräts fest
#API.device_set_operate_group_only(id, mode)
#  Legt die Bedienbarkeit des Geräts fest
#API.device_start_com_test(id)
#  Startet den Funktionstest für ein Gerät
#API.diagram_get_data_source_groups()
#  Ermittelt alle bekannten Gruppen von Datenquellen
#API.diagram_get_diagrams()
#  Ermittelt die zur Verfügung stehenden Messwert-Diagramme
#API.event_poll()
#  Fragt Ereignisse ab
#API.event_subscribe()
#  Anmeldung für Ereignisbenachrichtigungen
#API.event_unsubscribe()
#  Abmeldung für Ereignisbenachrichtigungen
#API.firewall_get_configuration()
#  Liefert die aktuelle Konfiguration der Firewall
#API.firewall_set_configuration(services, ips)
#  Setzt die Konfiguration der Firewall
#API.interface_activate_link_paramset(interface, address, peerAddress, longPress)
#  Aktiviert ein Link-Parameterset
#API.interface_add_device(interface, serialNumber)
#  Lernt ein Gerät anhand seiner Seriennummer an
#API.interface_add_link(interface, sender, receiver, name, description)
#  Erstellt eine direkte Verknüpfung
#API.interface_change_device(interface, addressNewDevice, addressOldDevice)
#  Tauscht ein Gerät gegen ein anderes aus.
#API.interface_change_key(interface, passphrase)
#  Ändert den AES-Schlüssel
#API.interface_clear_config_cache(interface, address)
#  Löscht die auf der HomeMatic Zentrale gespeicherten Konfigurationsdaten für ein Gerät
#API.interface_delete_device(interface, address, flags)
#  Löscht ein Gerät
#API.interface_determine_parameter(interface, address, paramsetKey, parameterId)
#  Bestimmt den Wert eines Patameters
#API.interface_get_device_description(interface, address)
#  Liefert die Beschreibung eines Geräts
#API.interface_get_install_mode(interface)
#  Liefert die Restzeit, für die der Anlernmodus noch aktiv ist
#API.interface_get_key_missmatch_device(interface, reset)
#  Liefert die Seriennummer des letzten Gerätes, welches nicht angelernt werden konnte
#API.interface_get_lgw_connection_status(interface, serial)
#  Liefert den Verbindungsstatus des BidCoS Wired Lan Gateways
#API.interface_get_lgw_status(interface)
#  Liefert den Status des BidCoS Wired Lan Gateways
#API.interface_get_link_info(interface, senderAddress, receiverAddress)
#  Liefert den Namen und die Beschreibung einer direkten Verknüpfung
#API.interface_get_link_peers(interface, address)
#  Liefert alle Kommukationspartner eines Geräts
#API.interface_get_links(interface, address, flags)
#  Liefert für ein Gerät oder einen Kanal alle dirketen Verknüpfungen
#API.interface_get_log_level(interface)
#  Liefert die aktuelle Stufe der Fehlerprotokollierung
#API.interface_get_master_value(interface, address, valueKey)
#  Liefert den Wert eines Parameters aus dem Parameterset "MASTER"
#API.interface_get_paramset(interface, address, paramsetKey)
#  Liefert ein komplettes Parameterset
#API.interface_get_paramset_description(interface, address, paramsetType)
#  Liefert die Beschreibung eines Parametersets
#API.interface_get_paramset_id(interface, address, paramsetType)
#  Liefert die Id eines Parametersets
#API.interface_get_service_message_count(interface)
#  Liefert die Anzahl der aktiven Servicemeldungen
#API.interface_get_value(interface, address, valueKey)
#  Liefert den Wert eines Parameters aus dem Parameterset "Values"
#API.interface_init(interface, url, interfaceId)
#  Meldet eine Logikschicht bei einer Schnittstelle an
#API.interface_is_present(interface)
#  Prüft, ob der Dienst der betreffenden Schnittstelle läuft)
#API.interface_list_bidcos_interfaces(interface)
#  Listet die verfügbaren BidCoS-RF Interfaces auf
#API.interface_list_devices(interface)
#  Liefert eine Liste aller angelernten Geräte
#API.interface_list_teams(interface)
#  Liefert die Gerätebeschreibungen aller Teams
#API.interface_put_paramset(interface, address, paramsetKey, set)
#  Schreibt ein komplettes Parameterset für ein Gerät
#API.interface_refresh_deployed_device_firmware_list(interface)
# Aktualisiert die Geraete-Firmware-Liste
#API.interface_remove_link(interface, sender, receiver)
#  Löscht eine direkte Verknüpfung
#API.interface_report_value_usage(interface, address, valueId, refCounter)
# Teilt der Schnittstelle mit, wie häufig die Logikschicht einen Wert verwendet
#API.interface_restore_config_to_device(interface, address)
#  Überträgt alle Konfigurationsdaten erneut an ein Gerät
#API.interface_rssi_info(interface)
#  Liefert die Empfangsfeldstärken der angeschlossenen Geräte
#API.interface_search_devices(interface)
#  Sucht auf dem Bus nach neuen Geräte
#API.interface_set_bidcos_interface(interface, deviceId, interfaceId, roaming)
#  Ordnet ein Geräte einem BidCoS-RF Interface zu
#API.interface_set_install_mode(interface, on)
#  Aktiviert oder dekativiert den Anlernmodus
#API.interface_set_link_info(interface, sender, receiver, name, description)
#  Legt den Namen und die Beschreibung einer direkten Verknüpfung fest
#API.interface_set_log_level(interface, level)
#  Legt die Stufe der Fehlerprotokollierung fest
#API.interface_set_team(inteface, channelAddress, teamAddress)
#  Fügt einem Team einen Kanal hinzu
#API.interface_set_temp_key(interface, passphrase)
#  Ändert den temporären AES-Schlüssel
#API.interface_set_value(interface, address, valueKey, type, value)
#  Setzt einen einzelnen Wert im Parameterset "Values"
#API.interface_update_firmware(interface, device)
#  Aktualisiert die Firmware der angegebenen Geräte
#API.program_delete_program_by_name(name)
#  Löscht ein Programm mit bestimmten Namen
#API.program_execute(id)
#  Führt ein Programm auf der HomeMatic Zentrale aus
#API.program_get(id)
#  Liefert Detailinformationen zu einem Programm auf der HomeMatic Zentrale
#API.program_get_all()
#  Liefert Detailinformationen zu allen Programmen auf der HomeMatic Zentrale
#API.rega_is_present()
#  Prüft, ob die Logikschicht (ReGa) aktiv ist
#API.rega_run_script(script)
#  Führt ein HomeMatic Script aus
#API.room_add_channel(id, channelId)
#  Fügt einen Kanal zu einem Raum hinzu
#API.room_list_program_ids(id)
#  Liefert die Ids aller Programme, die mindestens einen Kanal in dem Raum verwenden
#API.room_remove_channel(id, channelId)
#  Entfernt einen Kanal aus einem Raum
#API.safe_mode_enter()
#  Startet die HomeMatic Zentrale im angesicherten Modus
#API.session_login(username, password)
#  Führt die Benutzeranmeldung durch
#API.session_logout()
#  Beendet eine Sitzung
#API.session_renew()
#  Erneuert die Sitzung; Falls eine Sitzung nicht rechtzeitig erneuert wird, läuft diese ab
#API.session_set_session_var(var, val)
#  Setzt eine Session Variable
#API.subsection_add_channel(id, channelId)
#  Fügt dem Gewerk einen Kanal hinzu
#API.subsection_get(id)
#  Liefert Detailinformationen zu einem Gewerk
#API.subsection_get_all()
#  Liefert Detailinformationen zu allen Gewerken
#API.subsection_list_all()
#  Liefert eine Liste aller Gewerke
#API.subsection_list_program_ids(id)
#  Liefert die Ids aller Programme, die mindesten einen Kanal in dem Raum verwenden
#API.subsection_remove_channel(id, channelId)
#  Entfernt einen Kanal aus einem Gewerk
#API.sys_var_create_bool(name, init_val, internal)
#  Erzeugt eine Systemvariable vom Typ bool
#API.sys_var_create_float(name, minValue, maxValue, internal)
#  Erzeugt eine Systemvariable vom Typ Number
#API.sys_var_delete_sys_var_by_name(name)
#  Entfernt eine Systemvariable mit bestimmten Namen
#API.sys_var_get(id)
#  Liefert Detailinformationen zu einer Systemvariable auf der HomeMatic Zentrale
#API.sys_var_get_all()
#  Liefert Detailinformationen zu allen Systemvariablen auf der HomeMatic Zentrale
#API.sys_var_get_value(id)
#  Liefert den aktuellen Wert einer Systemvariable
#API.sys_var_get_value_by_name(name)
#  Liefert den aktuellen Wert einer Systemvariable
#API.sys_var_set_bool(name, value)
#  Setzt den Wert einer Systemvariable vom Type bool
#API.sys_var_set_float(name, value)
#  Setzt den Wert einer Systemvariable vom Type float
#API.system_describe()
#  Liefert eine detailierte Beschreibung der HomeMatic JSON API.
#API.system_get_energy_price()
#  Ermittelt den Preis einer KW/h
#API.system_list_methods()
#  Liefert eine Liste der verfügbaren Methoden
#API.system_method_help(name)
#  Liefert die Kurzbeschreibung einer Methode
#API.system_save_object_model()
#  Speichert das Object Model
#API.user_get_language(userName)
#  Ermittelt die gewählte Sprache des Benutzers
#API.user_get_user_name(userID)
#  Gibt den Username zurück
#API.user_is_no_expert(id)
#  Ermittelt, ob ein Benutzer Experte ist
#API.user_set_language(userName, userLang)
#  Setzt die gewählte Sprache des Benutzers
#API.web_ui_get_colors()
#  Liefert die Systemfarben der HomeMatic WebUI
