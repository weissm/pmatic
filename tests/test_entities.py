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
import time

import pmatic.api
import pmatic.utils as utils
import lib
from pmatic.entities import Entity, Device,HM_ES_PMSw1_Pl, \
                            ChannelClimaRegulator, \
                            device_classes_by_type_name, channel_classes_by_type_name, \
                            Channel,  Devices, \
                            ChannelShutterContact  
#                            ChannelKey 
from pmatic.params import ParameterFLOAT, ParameterACTION, ParameterBOOL #, ParameterINTEGER
from pmatic.ccu import CCUDevices
from pmatic.exceptions import PMException

class TestEntity(lib.TestCCUClassWide):
    def test_minimal_entity(self, ccu):
        Entity(ccu, {})

    def test_attributes(self, ccu):
        obj = Entity(ccu, {
            'ding_dong': 1,
            'BLA': 'blub', # keys are converted to lower case
            'blaBlubKey': 'XXX', # camel case conversion
        })

        assert obj.ding_dong == 1
        assert obj.bla == 'blub'
        assert obj.bla_blub_key == 'XXX'
        assert not hasattr(obj, "blaBlubKey")

    def test_attribute_conversion(self, ccu):
        def transform_with_ccu_obj(ccu, val):
            assert isinstance(ccu, pmatic.CCU)
            return val

        def transform_with_api_obj(api, val):
            assert isinstance(api, pmatic.api.RemoteAPI)
            return val

        def transform_with_device_obj(device, val):
            assert isinstance(device, Device)
            return val

        def transform_with_object_obj(obj, val):
            assert isinstance(obj, Entity)
            return val

        class TestDevice(Device):
            _transform_attributes = {
                "ding_dong"       : int,
                "ding_dong_float" : float,
                "XXX"             : transform_with_ccu_obj,
                "BLA"             : transform_with_api_obj,
                "BLUB"            : transform_with_device_obj,
                "HUH"             : transform_with_object_obj,
            }
            _mandatory_attributes = []

        obj = TestDevice(ccu, {
            'ding_dong': "1",
            'ding_dong_float': "1.0",
            'BLA': 'blub',
            'BLUB': 'dingeling',
            'HUH': 'hasbasl',
            'blah': 'blux',
        })

        assert obj.ding_dong == 1
        assert obj.ding_dong_float == 1.0
        assert obj.bla == "blub"
        assert obj.blub == "dingeling"
        assert obj.huh == "hasbasl"
        assert obj.blah == "blux"


    def test_mandatory_attributes(self, ccu):
        class TestEntity(Entity):
            _mandatory_attributes = [
                "dasda",
            ]

        obj = TestEntity(ccu, {
            'ding_dong': "1",
            'dasda': 'paff',
            'blah': 'blux',
        })

        assert obj.ding_dong == "1"
        assert obj.dasda == "paff"
        assert obj.blah == "blux"

        with pytest.raises(PMException) as e:
            TestEntity(ccu, {
                'ding_dong': "1",
                'blah': 'blux',
            })
        assert "mandatory attribute" in str(e)


class TestChannel(lib.TestCCUClassWide):
    @pytest.fixture(scope="function")
    def device(self, ccu):
        ccu.devices.clear() # don't let the CCUDevices() collection cache the object.
#        import traceback
#        print(b"".join(traceback.format_stack()[:-1]))

#        for device in ccu.devices.query():
#          print("%-20s %s %s %s" % (device.name, device.type, device.address, device.version))

#        for device in ccu.devices.query(device_type="HM-LC-Sw1-Pl"):
#          print("%-20s %s %s %s" % (device.name, device.type, device.address, device.version))

        device = list(ccu.devices.query(device_type="HM-LC-Sw1-Pl"))[0]
        return device


    @pytest.fixture(scope="function")
    def channel(self, device):
        return device.channels[1]


    def test_init(self, channel):
        assert isinstance(channel.device, Device)

        # Verify mandatory attributes
        assert hasattr(channel, "address")
        assert hasattr(channel, "direction")
        assert hasattr(channel, "flags")
        assert hasattr(channel, "index")
        assert hasattr(channel, "link_source_roles")
        assert hasattr(channel, "link_target_roles")
        assert hasattr(channel, "paramsets")
        assert hasattr(channel, "type")
        assert hasattr(channel, "version")

        # verify not having skip attributes
        assert not hasattr(channel, "parent")
        assert not hasattr(channel, "parent_type")


    def test_init_with_invalid_device(self):
        with pytest.raises(PMException) as e:
            Channel(None, {})
        assert "not a Device derived" in str(e)


    def test_from_channel_dicts(self, ccu):
        device = Device(ccu, {
            'address': 'KEQ0970393',
            'firmware': '1.4',
            'flags': 1,
            'interface': 'KEQ0714972',
            'roaming': False,
            'type': 'HM-ES-PMSw1-Pl',
            'updatable': '1',
            'version': 1,
            'channels': [],
        })

        channels = Channel.from_channel_dicts(device, [
            {
                'address': 'KEQ0970393:1',
                'direction': 1,
                'flags': 1,
                'index': 1,
                'link_source_roles': [
                    'KEYMATIC',
                    'SWITCH',
                    'WINDOW_SWITCH_RECEIVER',
                    'WINMATIC'
                ],
                'link_target_roles': [],
                'paramsets': ['LINK', 'MASTER', 'VALUES'],
                'type': 'SHUTTER_CONTACT',
                'version': 15,
            },
            {
                'address': 'KEQ0970393:2',
                'direction': 1,
                'flags': 1,
                'index': 2,
                'link_source_roles': [
                    'KEYMATIC',
                    'SWITCH',
                    'WINDOW_SWITCH_RECEIVER',
                    'WINMATIC'
                ],
                'link_target_roles': [],
                'paramsets': ['LINK', 'MASTER', 'VALUES'],
                'type': 'SHUTTER_CONTACT',
                'version': 15,
            }
        ])

        assert len(channels) == 2
        assert 0 not in channels
        assert isinstance(channels[1], ChannelShutterContact)
        assert isinstance(channels[2], ChannelShutterContact)



    def test_channel_unknown_type(self, capfd, ccu):
        # Set loglevel so that we get the debug message
        pmatic.logging(pmatic.DEBUG)

        device = Device(ccu, {
            'address': 'KEQ0970393',
            'firmware': '1.4',
            'flags': 1,
            'interface': 'KEQ0714972',
            'roaming': False,
            'type': 'HM-ES-PMSw1-Pl',
            'updatable': '1',
            'version': 1,
            'channels': [],
        })

        Channel.from_channel_dicts(device, [
            {
                'address': 'KEQ0970393:1',
                'direction': 1,
                'flags': 1,
                'index': 1,
                'link_source_roles': [
                    'KEYMATIC',
                    'SWITCH',
                    'WINDOW_SWITCH_RECEIVER',
                    'WINMATIC'
                ],
                'link_target_roles': [],
                'paramsets': ['LINK', 'MASTER', 'VALUES'],
                'type': 'XXX_SHUTTER_CONTACT',
                'version': 15,
            }
        ])

        out, err = capfd.readouterr()
        assert "Using generic" in err
        assert "XXX_SHUTTER_CONTACT" in err
        assert out == ""

        # revert to default log level
        pmatic.logging()


    def test_values(self, channel):
        assert channel._values == {}

        assert len(channel.values) > 6

        assert isinstance(channel.values["INHIBIT"], ParameterBOOL)
        assert isinstance(channel.values["INSTALL_TEST"], ParameterACTION)
#        assert isinstance(channel.values["ON_TIME"], ParameterFLOAT)
        assert isinstance(channel.values["WORKING"], ParameterBOOL)
        assert isinstance(channel.values["STATE"], ParameterBOOL)
        assert isinstance(channel.values["PRESS_LONG"], ParameterACTION)
        assert isinstance(channel.values["PRESS_SHORT"], ParameterACTION)
        assert isinstance(channel.values["LEVEL"], ParameterFLOAT)

        assert len(channel._values) > 0

        # when more than X seconds old, an update is needed. Test this!
        update_needed_time = time.time() - 60
        for val in channel.values.values():
            val._value_updated = update_needed_time

        assert len(channel.values)

        for val in channel.values.values():
            if val.readable:
                assert val.last_updated != update_needed_time


    def test_value_update_needed(self, channel):
        channel._values = {}
        assert len(channel.values) > 0

        p = channel.values["STATE"]
        assert not channel._value_update_needed()

        p._value_updated = None
        assert channel._value_update_needed()

        p._value_updated = time.time()
        assert not channel._value_update_needed()

        p._value_updated = time.time() - 50
        assert not channel._value_update_needed()

        p._value_updated = time.time() - 60
        assert channel._value_update_needed()


    def test_fetch_values(self, channel):
        channel._values = {}
        with pytest.raises(PMException) as e:
            channel._fetch_values()
        assert "not yet initialized" in str(e)

        assert len(channel.values) > 0
        channel._fetch_values()


    def test_get_values_single_fallback(self, device, channel, monkeypatch):
        channel._values = {}

        def raise_invalid_value():
            raise PMException("blabla 601 bla")

        def catch_get_values_single(skip_invalid_values):
            assert skip_invalid_values == True
            raise Exception("YEP!")

        monkeypatch.setattr(channel, "_get_values_bulk", raise_invalid_value)
        monkeypatch.setattr(channel, "_get_values_single", catch_get_values_single)

        channel._init_value_specs()

        with pytest.raises(Exception) as e:
            channel._fetch_values()
        assert "YEP!" in "%s" % e


    def test_get_values_single(self, channel):
        channel._values = {}
        channel._init_value_specs()

        # channel.interface = "HmIP-RF"
        # channel.address = "001718A9A77FBC"
        # raw_values = channel._get_values_single()
        # print(self.values)

        raw_values = channel._get_values_bulk()
        assert len(raw_values) >= 3

        assert "INHIBIT" in raw_values
        assert "WORKING" in raw_values
        assert "STATE" in raw_values


    def test_get_values_single_with_invalid(self, channel, device, monkeypatch):
        channel._values = {}
        channel._init_value_specs()
        maintenance = device.channels[0]

        def raise_invalid_value(*args, **kwargs):
            raise PMException("bla 601 bla")
        monkeypatch.setattr(channel._ccu.api, "interface_get_value", raise_invalid_value)

        with pytest.raises(PMException) as e:
            channel._get_values_single()
        assert "bla 601 bla" in "%s" % e

        raw_values = channel._get_values_single(skip_invalid_values=True)
        assert raw_values == {}

        with pytest.raises(PMException) as e:
            maintenance._get_values_single()
        assert "bla 601 bla" in "%s" % e

        raw_values = maintenance._get_values_single(skip_invalid_values=True)
        assert raw_values == {}


    def test_get_values_single_with_invalid_offline(self, channel, device, monkeypatch):
        channel._values = {}
        channel._init_value_specs()
        maintenance = device.channels[0]

        monkeypatch.setattr(maintenance.values["UNREACH"], "_value", True)

        def raise_invalid_value(*args, **kwargs):
            raise PMException("bla 601 bla")
        monkeypatch.setattr(channel._ccu.api, "interface_get_value", raise_invalid_value)

        with pytest.raises(PMException) as e:
            channel._get_values_single()
        assert "bla 601 bla" in "%s" % e

        with pytest.raises(PMException) as e:
            channel._get_values_single(skip_invalid_values=True)
        assert "bla 601 bla" in "%s" % e

        with pytest.raises(PMException) as e:
            maintenance._get_values_single()
        assert "bla 601 bla" in "%s" % e

        raw_values = maintenance._get_values_single(skip_invalid_values=True)
        assert raw_values == {}


    def test_get_values_single_with_random_exc(self, channel, device, monkeypatch):
        channel._values = {}
        channel._init_value_specs()
        maintenance = device.channels[0]
        maintenance._init_value_specs()

        def raise_random_exception(*args, **kwargs):
            raise Exception("blub")
        monkeypatch.setattr(channel._ccu.api, "interface_get_value", raise_random_exception)

        with pytest.raises(Exception) as e:
            channel._get_values_single()
        assert "blub" in "%s" % e

        with pytest.raises(Exception) as e:
            channel._get_values_single(skip_invalid_values=True)
        assert "blub" in "%s" % e

        with pytest.raises(Exception) as e:
            maintenance._get_values_single()
        assert "blub" in "%s" % e

        with pytest.raises(Exception) as e:
            maintenance._get_values_single(skip_invalid_values=True)
        assert "blub" in "%s" % e


    def test_summary_state(self, ccu):
        device = list(ccu.devices.query(device_type="HM-LC-Sw1-Pl"))[0]
        assert device.summary_state != ""
        assert utils.is_text(device.summary_state)
        assert device.summary_state.count(",") == 15
        assert device.summary_state.count(":") == 16


    # FIXME: Test
    # - set_logic_attributes


    def test_on_value_changed(self, channel):
        def x(param): # pylint:disable=unused-argument
            raise PMException("DING")

        channel.on_value_changed(x)

        p = channel.values[list(channel.values.keys())[0]]
        assert x in p._get_callbacks("value_changed")
        assert x not in p._get_callbacks("value_updated")

        with pytest.raises(PMException) as e:
            p._callback("value_changed")
        assert "DING" in str(e)


    def test_on_value_updated(self, channel):
        def x(param): # pylint:disable=unused-argument
            raise PMException("DING")

        channel.on_value_updated(x)

        p = channel.values[list(channel.values.keys())[0]]
        assert x in p._get_callbacks("value_updated")
        assert x not in p._get_callbacks("value_changed")

        with pytest.raises(PMException) as e:
            p._callback("value_updated")
        assert "DING" in str(e)


    # FIXME: Add tests for _save_callback_to_register, _register_saved_callbacks

class TestChannelCCU2(lib.TestCCUClassWideCCU2):
    @pytest.fixture(scope="function")
    def device(self, ccu2):
        ccu2.devices.clear() # don't let the CCUDevices() collection cache the object.
        device = list(ccu2.devices.query(device_address="KEQ0970393"))[0]
        return device


    @pytest.fixture(scope="function")
    def channel(self, device):
        return device.channels[1]


    def test_init(self, channel):
        assert isinstance(channel.device, Device)

        # Verify mandatory attributes
        assert hasattr(channel, "address")
        assert hasattr(channel, "direction")
        assert hasattr(channel, "flags")
        assert hasattr(channel, "index")
        assert hasattr(channel, "link_source_roles")
        assert hasattr(channel, "link_target_roles")
        assert hasattr(channel, "paramsets")
        assert hasattr(channel, "type")
        assert hasattr(channel, "version")

        # verify not having skip attributes
        assert not hasattr(channel, "parent")
        assert not hasattr(channel, "parent_type")


    def test_init_with_invalid_device(self):
        with pytest.raises(PMException) as e:
            Channel(None, {})
        assert "not a Device derived" in str(e)


    def test_from_channel_dicts(self, ccu2):
        device = Device(ccu2, {
            'address': 'KEQ0970393',
            'firmware': '1.4',
            'flags': 1,
            'interface': 'KEQ0714972',
            'roaming': False,
            'type': 'HM-ES-PMSw1-Pl',
            'updatable': '1',
            'version': 1,
            'channels': [],
        })

        channels = Channel.from_channel_dicts(device, [
            {
                'address': 'KEQ0970393:1',
                'direction': 1,
                'flags': 1,
                'index': 1,
                'link_source_roles': [
                    'KEYMATIC',
                    'SWITCH',
                    'WINDOW_SWITCH_RECEIVER',
                    'WINMATIC'
                ],
                'link_target_roles': [],
                'paramsets': ['LINK', 'MASTER', 'VALUES'],
                'type': 'SHUTTER_CONTACT',
                'version': 15,
            },
            {
                'address': 'KEQ0970393:2',
                'direction': 1,
                'flags': 1,
                'index': 2,
                'link_source_roles': [
                    'KEYMATIC',
                    'SWITCH',
                    'WINDOW_SWITCH_RECEIVER',
                    'WINMATIC'
                ],
                'link_target_roles': [],
                'paramsets': ['LINK', 'MASTER', 'VALUES'],
                'type': 'SHUTTER_CONTACT',
                'version': 15,
            }
        ])

        assert len(channels) == 2
        assert 0 not in channels
        assert isinstance(channels[1], ChannelShutterContact)
        assert isinstance(channels[2], ChannelShutterContact)



    def test_channel_unknown_type(self, capfd, ccu2):
        # Set loglevel so that we get the debug message
        pmatic.logging(pmatic.DEBUG)

        device = Device(ccu2, {
            'address': 'KEQ0970393',
            'firmware': '1.4',
            'flags': 1,
            'interface': 'KEQ0714972',
            'roaming': False,
            'type': 'HM-ES-PMSw1-Pl',
            'updatable': '1',
            'version': 1,
            'channels': [],
        })

        Channel.from_channel_dicts(device, [
            {
                'address': 'KEQ0970393:1',
                'direction': 1,
                'flags': 1,
                'index': 1,
                'link_source_roles': [
                    'KEYMATIC',
                    'SWITCH',
                    'WINDOW_SWITCH_RECEIVER',
                    'WINMATIC'
                ],
                'link_target_roles': [],
                'paramsets': ['LINK', 'MASTER', 'VALUES'],
                'type': 'XXX_SHUTTER_CONTACT',
                'version': 15,
            }
        ])

        out, err = capfd.readouterr()
        assert "Using generic" in err
        assert "XXX_SHUTTER_CONTACT" in err
        assert out == ""

        # revert to default log level
        pmatic.logging()


    def test_values(self, channel):
        assert channel._values == {}

        assert len(channel.values) == 5

        assert isinstance(channel.values["INHIBIT"], ParameterBOOL)
        assert isinstance(channel.values["INSTALL_TEST"], ParameterACTION)
        assert isinstance(channel.values["ON_TIME"], ParameterFLOAT)
        assert isinstance(channel.values["WORKING"], ParameterBOOL)
        assert isinstance(channel.values["STATE"], ParameterBOOL)

        assert len(channel._values) == 5

        # when more than X seconds old, an update is needed. Test this!
        update_needed_time = time.time() - 60
        for val in channel.values.values():
            val._value_updated = update_needed_time

        assert len(channel.values)

        for val in channel.values.values():
            if val.readable:
                assert val.last_updated != update_needed_time


    def test_value_update_needed(self, channel):
        channel._values = {}
        assert len(channel.values) == 5

        p = channel.values["STATE"]
        assert not channel._value_update_needed()

        p._value_updated = None
        assert channel._value_update_needed()

        p._value_updated = time.time()
        assert not channel._value_update_needed()

        p._value_updated = time.time() - 50
        assert not channel._value_update_needed()

        p._value_updated = time.time() - 60
        assert channel._value_update_needed()


    def test_fetch_values(self, channel):
        channel._values = {}
        with pytest.raises(PMException) as e:
            channel._fetch_values()
        assert "not yet initialized" in str(e)

        assert len(channel.values) == 5
        channel._fetch_values()


    def test_get_values_single_fallback(self, device, channel, monkeypatch):
        channel._values = {}

        def raise_invalid_value():
            raise PMException("blabla 601 bla")

        def catch_get_values_single(skip_invalid_values):
            assert skip_invalid_values == True
            raise Exception("YEP!")

        monkeypatch.setattr(channel, "_get_values_bulk", raise_invalid_value)
        monkeypatch.setattr(channel, "_get_values_single", catch_get_values_single)

        channel._init_value_specs()

        with pytest.raises(Exception) as e:
            channel._fetch_values()
        assert "YEP!" in "%s" % e


    def test_get_values_single(self, channel):
        channel._values = {}
        channel._init_value_specs()

        raw_values = channel._get_values_single()
        assert len(raw_values) == 3

        assert "INHIBIT" in raw_values
        assert "WORKING" in raw_values
        assert "STATE" in raw_values


    def test_get_values_single_with_invalid(self, channel, device, monkeypatch):
        channel._values = {}
        channel._init_value_specs()
        maintenance = device.channels[0]

        def raise_invalid_value(*args, **kwargs):
            raise PMException("bla 601 bla")
        monkeypatch.setattr(channel._ccu.api, "interface_get_value", raise_invalid_value)

        with pytest.raises(PMException) as e:
            channel._get_values_single()
        assert "bla 601 bla" in "%s" % e

        raw_values = channel._get_values_single(skip_invalid_values=True)
        assert raw_values == {}

        with pytest.raises(PMException) as e:
            maintenance._get_values_single()
        assert "bla 601 bla" in "%s" % e

        raw_values = maintenance._get_values_single(skip_invalid_values=True)
        assert raw_values == {}


    def test_get_values_single_with_invalid_offline(self, channel, device, monkeypatch):
        channel._values = {}
        channel._init_value_specs()
        maintenance = device.channels[0]

        monkeypatch.setattr(maintenance.values["UNREACH"], "_value", True)

        def raise_invalid_value(*args, **kwargs):
            raise PMException("bla 601 bla")
        monkeypatch.setattr(channel._ccu.api, "interface_get_value", raise_invalid_value)

        with pytest.raises(PMException) as e:
            channel._get_values_single()
        assert "bla 601 bla" in "%s" % e

        with pytest.raises(PMException) as e:
            channel._get_values_single(skip_invalid_values=True)
        assert "bla 601 bla" in "%s" % e

        with pytest.raises(PMException) as e:
            maintenance._get_values_single()
        assert "bla 601 bla" in "%s" % e

        raw_values = maintenance._get_values_single(skip_invalid_values=True)
        assert raw_values == {}


    def test_get_values_single_with_random_exc(self, channel, device, monkeypatch):
        channel._values = {}
        channel._init_value_specs()
        maintenance = device.channels[0]
        maintenance._init_value_specs()

        def raise_random_exception(*args, **kwargs):
            raise Exception("blub")
        monkeypatch.setattr(channel._ccu.api, "interface_get_value", raise_random_exception)

        with pytest.raises(Exception) as e:
            channel._get_values_single()
        assert "blub" in "%s" % e

        with pytest.raises(Exception) as e:
            channel._get_values_single(skip_invalid_values=True)
        assert "blub" in "%s" % e

        with pytest.raises(Exception) as e:
            maintenance._get_values_single()
        assert "blub" in "%s" % e

        with pytest.raises(Exception) as e:
            maintenance._get_values_single(skip_invalid_values=True)
        assert "blub" in "%s" % e


    def test_summary_state(self, ccu2):
        device = list(ccu2.devices.query(device_type="HM-ES-PMSw1-Pl"))[0]
        assert device.summary_state != ""
        assert utils.is_text(device.summary_state)
        assert device.summary_state.count(",") == 6
        assert device.summary_state.count(":") == 7


    # FIXME: Test
    # - set_logic_attributes


    def test_on_value_changed(self, channel):
        def x(param): # pylint:disable=unused-argument
            raise PMException("DING")

        channel.on_value_changed(x)

        p = channel.values[list(channel.values.keys())[0]]
        assert x in p._get_callbacks("value_changed")
        assert x not in p._get_callbacks("value_updated")

        with pytest.raises(PMException) as e:
            p._callback("value_changed")
        assert "DING" in str(e)


    def test_on_value_updated(self, channel):
        def x(param): # pylint:disable=unused-argument
            raise PMException("DING")

        channel.on_value_updated(x)

        p = channel.values[list(channel.values.keys())[0]]
        assert x in p._get_callbacks("value_updated")
        assert x not in p._get_callbacks("value_changed")

        with pytest.raises(PMException) as e:
            p._callback("value_updated")
        assert "DING" in str(e)



class TestChannelMaintenance(lib.TestCCUClassWide):
    @pytest.fixture(scope="function")
    def device(self, ccu):
        return list(ccu.devices.query(device_name="Rev iComfort"))[0]


    @pytest.fixture(scope="function")
    def m(self, device):
        return device.maintenance


    def test_summary_state(self, m):
        assert m.summary_state == None


    def test_maintenance_state(self, m):
        assert m.maintenance_state != ""
        assert utils.is_text(m.maintenance_state)
        assert m.maintenance_state.count(",") == 2
        assert m.maintenance_state.count(":") == 3


class TestChannelSwitchTransmit(lib.TestCCUClassWide):
    @pytest.fixture(scope="function")
    def device(self, ccu):
        d = Device(ccu, {
            'address': u'LEQ0079034',
            'available_firmware': '1.3',
            'firmware': '1.3',
            'flags': 1,
            'interface': 'MEQ0835974',
            'paramsets': ['MASTER'],
            'roaming': False,
            'type': 'HM-TC-IT-WM-W-E',
            'updatable': '1',
            'version': 21,
            'children': ['LEQ0079034:0',
                          'LEQ0079034:1',
                          'LEQ0079034:2',
                          'LEQ0079034:3',
                          'LEQ0079034:6',
                          'LEQ0079034:7'],
            'channels': [
                {'address': 'LEQ0079034:0',
                 'aes_active': False,
                 'direction': 0,
                 'flags': 3,
                 'index': 0,
                 'link_source_roles': [],
                 'link_target_roles': [],
                 'paramsets': ['MASTER', 'VALUES'],
                 'parent': 'LEQ0079034',
                 'parent_type': 'HM-TC-IT-WM-W-E',
                 'type': 'MAINTENANCE',
                 'version': 21},
                {'address': 'LEQ0079034:1',
                 'aes_active': False,
                 'direction': 1,
                 'flags': 1,
                 'index': 1,
                 'link_source_roles': ['WEATHER_TH'],
                 'link_target_roles': [],
                 'paramsets': ['LINK', 'VALUES'],
                 'parent': 'LEQ0079034',
                 'parent_type': 'HM-TC-IT-WM-W-E',
                 'type': 'WEATHER_TRANSMIT',
                 'version': 21},
                {'address': 'LEQ0079034:2',
                 'aes_active': False,
                 'direction': 1,
                 'flags': 1,
                 'index': 2,
                 'link_source_roles': ['THERMALCONTROL_TC'],
                 'link_target_roles': [],
                 'paramsets': ['LINK', 'VALUES'],
                 'parent': 'LEQ0079034',
                 'parent_type': 'HM-TC-IT-WM-W-E',
                 'type': 'THERMALCONTROL_TRANSMIT',
                 'version': 21},
                {'address': 'LEQ0079034:3',
                 'aes_active': False,
                 'direction': 2,
                 'flags': 1,
                 'index': 3,
                 'link_source_roles': [],
                 'link_target_roles': ['WINDOW_SWITCH_RECEIVER',
                                        'WINDOW_SWITCH_RECEIVER_V2'],
                 'paramsets': ['LINK', 'MASTER', 'VALUES'],
                 'parent': 'LEQ0079034',
                 'parent_type': 'HM-TC-IT-WM-W-E',
                 'type': 'WINDOW_SWITCH_RECEIVER',
                 'version': 21},
                {'address': 'LEQ0079034:6',
                 'aes_active': False,
                 'direction': 2,
                 'flags': 1,
                 'index': 6,
                 'link_source_roles': [],
                 'link_target_roles': ['REMOTECONTROL_RECEIVER'],
                 'paramsets': ['LINK', 'MASTER', 'VALUES'],
                 'parent': 'LEQ0079034',
                 'parent_type': 'HM-TC-IT-WM-W-E',
                 'type': 'REMOTECONTROL_RECEIVER',
                 'version': 21},
                {'address': 'LEQ0079034:7',
                 'aes_active': False,
                 'direction': 1,
                 'flags': 1,
                 'index': 7,
                 'link_source_roles': ['SWITCH'],
                 'link_target_roles': [],
                 'paramsets': ['LINK', 'MASTER', 'VALUES'],
                 'parent': 'LEQ0079034',
                 'parent_type': 'HM-TC-IT-WM-W-E',
                 'type': 'SWITCH_TRANSMIT',
                 'version': 21}
            ],
        })

        # Just the value spec we like to test
        d.channels[7]._init_value_spec({
            "NAME": "DECISION_VALUE",
            "DEFAULT": "0",
            "FLAGS": "1",
            "ID": "DECISION_VALUE",
            "MAX": "255",
            "MIN": "0",
            "OPERATIONS": "5",
            "TAB_ORDER": "0",
            "TYPE": "INTEGER",
            "UNIT":""
        })
        return d


    def test_mode_fix(self, device):
        c = device.channels[7]
        assert c.values["DECISION_VALUE"].readable == False
        assert c.values["DECISION_VALUE"].writable == False
        assert c.values["DECISION_VALUE"].supports_events == True


    def test_mode_fix_fetch_values(self, device, monkeypatch):
        c = device.channels[7]
        monkeypatch.setattr(c, "_get_values_single", lambda: "SINGLE")
        assert c._get_values() == "SINGLE"




class TestDevices(lib.TestCCUClassWide):
    @pytest.fixture(scope="function")
    def devices(self, ccu):
        return Devices(ccu)


    def test_init(self, ccu):
        Devices(ccu)
        with pytest.raises(PMException):
            Devices(None)


    def test_get_all(self, ccu, devices):
        assert list(devices) == []
        assert len(devices) == 0
        assert isinstance(devices._device_dict, dict)
        assert len(devices._device_dict) == 0

        result1 = ccu.devices.query(device_type="HM-LC-Sw1-Pl")
        devices.add(list(result1)[0])
        assert len(devices) == 1
        assert len(devices._device_dict) == 1


    def test_add(self, ccu, devices):
        device1 = list(ccu.devices)[0]

        if isinstance(self, TestCCUDevices):
            ccu.devices.delete(device1.address)
            expected_len = len(ccu.devices)+1
        else:
            expected_len = 1

        devices.add(device1)
        assert len(devices) == expected_len

        with pytest.raises(PMException):
            devices.add(None)

        assert len(devices) == expected_len


    def test_exists(self, ccu, devices):
        device = list(ccu.devices)[0]
        assert not devices.exists(device.address)
        devices.add(device)
        assert devices.exists(device.address)
        assert not devices.exists(device.address+"x")


    def test_addresses(self, ccu, devices):
        device1 = list(ccu.devices)[0]
        devices.add(device1)

        if utils.is_py2():
            assert isinstance(devices.addresses(), list)
        else:
            assert isinstance(list(devices.addresses()), list)

        assert len(devices.addresses()) == 1
        if utils.is_py2():
            assert devices.addresses() == [device1.address]
        else:
            assert list(devices.addresses()) == [device1.address]


    def test_delete(self, ccu, devices):
        device1 = list(ccu.devices)[0]
        devices.add(device1)

        assert len(devices) == 1
        devices.delete(device1.address)
        assert len(devices) == 0

        devices.delete("xxx123")


    def test_clear(self, ccu, devices):
        assert len(devices) == 0
        devices.clear()
        assert len(devices) == 0

        device1 = list(ccu.devices)[0]
        devices.add(device1)

        assert len(devices) == 1
        devices.clear()
        assert len(devices) == 0


    def test_get_device_or_channel_by_address(self, ccu, devices):
        device1 = list(ccu.devices)[0]
        devices.add(device1)

        dev = devices.get_device_or_channel_by_address(device1.address)
        assert isinstance(dev, Device)
        assert dev.address == device1.address

        chan = devices.get_device_or_channel_by_address(device1.address+":1")
        assert isinstance(chan, Channel)
        assert chan.address != device1.address

        with pytest.raises(KeyError):
            devices.get_device_or_channel_by_address(device1.address+":99")

        with pytest.raises(KeyError):
            devices.get_device_or_channel_by_address("xxxxxxx")



class TestCCUDevices(TestDevices):
    @pytest.fixture(scope="function")
    def devices(self, ccu):
        return CCUDevices(ccu)


    def test_ccu_devices_wrong_init(self):
        with pytest.raises(PMException):
            return CCUDevices(None)


    def test_get_all(self, ccu, devices):
        assert len(devices._device_dict) == 0
        assert list(devices) != []
        all_len = len(devices)
        assert all_len > 0
        assert isinstance(devices._device_dict, dict)
        assert len(devices._device_dict) > 0

        result1 = ccu.devices.query(device_type="HM-LC-Sw1-Pl")
        devices.add(list(result1)[0])
        assert len(devices) == all_len


    def test_query(self, ccu):
        ccu.devices.clear()
        assert len(ccu.devices._device_dict) == 0

        result1 = ccu.devices.query(device_type="HM-LC-Sw1-Pl")
        assert len(result1) > 0

        assert len(ccu.devices._device_dict) == len(result1)

        result2 = ccu.devices.query(device_type="xxx")
        assert len(result2) == 0

        result3 = ccu.devices.query(device_type="HmIP-SWDM")
        assert len(result3) > 0

        result4 = ccu.devices.query(device_name_regex="^%$")
        assert len(result4) == 0

        result5 = ccu.devices.query(device_name_regex="^Wohnzimmer.*$")
        assert len(result5) > 0

        result6 = ccu.devices.query(device_address="")
        assert len(result6) == 0

        result7 = ccu.devices.query(device_address="001718A9A77FBC")
        assert len(result7) > 0

        all_returned = list(set(list(result1) + list(result3) + list(result5) + list(result7)))

        assert len(ccu.devices._device_dict) == len(all_returned)


    def test_create_from_low_level_dict(self, API, devices):
        device1 = list(pmatic.api.DeviceSpecs(API).values())[0]
        device = devices._create_from_low_level_dict(device1)

        assert isinstance(device, Device)
        assert device.address == device1["address"]
        assert utils.is_text(device.name)
        assert device.name != ""


    def test_add_from_low_level_dict(self, API, devices):
        device1_dict = list(pmatic.api.DeviceSpecs(API).values())[0]
        expected_len = len(devices)

        devices.delete(device1_dict["address"])
        assert len(devices) == expected_len-1

        devices.add_from_low_level_dict(device1_dict)
        assert len(devices) == expected_len


    def test_exists(self, ccu, devices):
        device = list(ccu.devices)[0]
        assert devices.exists(device.address)
        devices.delete(device.address)
        assert not devices.exists(device.address)
        assert not devices.exists(device.address+"x")


    def test_addresses(self, ccu, devices):
        if utils.is_py2():
            assert isinstance(devices.addresses(), list)
        else:
            assert isinstance(list(devices.addresses()), list)

        assert len(devices.addresses()) > 0

        for address in devices.addresses():
            assert len(address) >= 9 or address == "BidCoS-RF"


    def test_delete(self, ccu, devices):
        device1 = list(ccu.devices)[0]
        expected_len = len(devices)-1

        devices.delete(device1.address)
        assert len(devices) == expected_len

        devices.delete("xxx123")
        assert len(devices) == expected_len


    def test_clear(self, ccu, devices): # pylint:disable=unused-argument
        assert len(devices._device_dict) == 0
        assert len(devices) > 0
        devices.clear()
        assert len(devices._device_dict) == 0


    def test_get_device_or_channel_by_address(self, ccu, devices):
        device1 = list(ccu.devices)[0]
        devices.add(device1)

        dev = devices.get_device_or_channel_by_address(device1.address)
        assert isinstance(dev, Device)
        assert dev.address == device1.address

        chan = devices.get_device_or_channel_by_address(device1.address+":1")
        assert isinstance(chan, Channel)
        assert chan.address != device1.address

        with pytest.raises(KeyError):
            devices.get_device_or_channel_by_address(device1.address+":99")

        with pytest.raises(KeyError):
            devices.get_device_or_channel_by_address("xxxxxxx")


    def test_already_initialized_devices(self, ccu):
        ccu.devices.clear()
        assert len(ccu.devices.already_initialized_devices) == 0

        result1 = ccu.devices.query(device_type="HM-LC-Sw1-Pl")
        assert len(result1) > 0

        assert len(ccu.devices.already_initialized_devices) == len(result1)



class TestDevice(lib.TestCCUClassWide):
    @pytest.fixture(scope="class")
    def d(self, ccu):
        return list(ccu.devices.query(device_name="Wohnzimmertisch gross"))[0]


    def test_is_online(self, d):
        assert d.is_online == True

        d.maintenance.values["UNREACH"]._value = True
        assert d.is_online == True

        orig_ty = d.type
        d.type = "HM-RCV-50"
        d.maintenance.values["UNREACH"]._value = False
        assert d.is_online == True

        d.maintenance.values["UNREACH"]._value = True
        assert d.is_online == True

        d.type = orig_ty


    def test_has_pending_config(self, d):
        assert d.has_pending_config == False

        d.maintenance.values["CONFIG_PENDING"]._value = True
        assert d.has_pending_config == False ## Fixme: check wrong behavior

        orig_ty = d.type
        d.type = "HM-RCV-50"
        d.maintenance.values["CONFIG_PENDING"]._value = True
        assert d.has_pending_config == False

        d.maintenance.values["CONFIG_PENDING"]._value = False
        assert d.has_pending_config == False

        d.type = orig_ty


    def test_has_pending_update(self, d):
        assert d.has_pending_update == False

        d.maintenance.values["UPDATE_PENDING"]._value = True
        assert d.has_pending_update == False ## Fixme: check wrong behavior

        sav = d.maintenance.values["UPDATE_PENDING"]
        del d.maintenance.values["UPDATE_PENDING"]

        assert d.has_pending_update == False

        d.maintenance.values["UPDATE_PENDING"] = sav

    # FIXME: Add missing tests!


# # FIXME: cannot test, no device w/ this behavior
# class TestHM_CC_RT_DN(lib.TestCCUClassWideCCU2):
    # @pytest.fixture(scope="class")
    # def d(self, ccu2):
        # print("hier: ", ccu2.devices)
        # return list(ccu2.devices.query(device_name="Wohnzimmer"))[0]


    # def test_temperature(self, d):
        # assert type(d.temperature) == ParameterFLOAT
        # assert isinstance(d.temperature.value, float)
        # assert utils.is_string("%s" % d.temperature)


    # def test_set_temperature(self, d):
        # assert type(d.set_temperature) == ParameterFLOAT
        # assert isinstance(d.set_temperature.value, float)
        # assert utils.is_string("%s" % d.set_temperature)


    # def test_is_off(self, d):
        # assert d.set_temperature._set_value(10.5)
        # assert d.is_off == False
        # assert d.set_temperature._set_value(4.5)
        # assert d.is_off == True


    # def test_change_temperature(self, d):
        # prev_temp = d.set_temperature.value

        # d.set_temperature = 9.5
        # assert d.set_temperature == 9.5

        # d.set_temperature_comfort()
        # # if not lib.is_testing_with_real_ccu():
        # d.set_temperature._value = 20.0
        # assert d.set_temperature != 9.5

        # d.set_temperature = 9.5

        # d.set_temperature_lowering()
        # # if not lib.is_testing_with_real_ccu():
        # d.set_temperature._value = 10.0
        # assert d.set_temperature != 9.5

        # d.set_temperature = prev_temp


    # def test_turn_off(self, d):
        # prev_temp = d.set_temperature.value

        # d.turn_off()
        # assert d.is_off == True

        # d.set_temperature = prev_temp


    # def test_control_mode(self, d, monkeypatch):
        # # Test setting invalid control mode
        # with pytest.raises(PMException) as e:
            # d.control_mode = "BIMBAM"
        # assert "must be one of" in str(e)

        # def set_mode(mode):
            # d.control_mode = mode

            # # Fake the value for testing without CCU. When testing with CCU, this
            # # value is fetched fresh from the CCU.
# #            if not lib.is_testing_with_real_ccu():
            # d.control_mode._value = mode

            # if mode == "BOOST":
                # d.boost_duration._value = 5

            # # In my tests it took some time to apply the new mode. Wait for 10 seconds
            # # maximum after setting the new mode.
            # for i in range(20):
                # if d.control_mode == mode:
                    # break
                # time.sleep(1)

            # assert d.control_mode == mode

        # # When testing without CCU the values must not be refetched because
        # # the API calls for reading the values are always using the same parameter
        # # set, but should return different states. This is currently not supported
        # # by the recorded CCU transaction mechanism.
        # # if not lib.is_testing_with_real_ccu():
        # monkeypatch.setattr(d.channels[4], "_value_update_needed", lambda: False)

        # # Ensure consistent initial state
        # set_mode("AUTO")
        # d.set_temperature = 20.0

        # prev_temp = d.set_temperature.value
        # set_mode("MANUAL")

        # assert d.set_temperature.value == prev_temp

        # d.turn_off()
        # assert d.is_off == True

        # set_mode("MANUAL")
        # assert d.set_temperature.value == d.set_temperature.default

        # assert d.boost_duration == None
        # set_mode("BOOST")

        # assert type(d.boost_duration) == ParameterINTEGER
        # assert d.boost_duration < 6

        # # FIXME: TEst party mode
        # set_mode("AUTO")


    # def test_is_battery_low(self, d):
        # assert d.is_battery_low == False
        # p = d.channels[4].values["FAULT_REPORTING"]
        # val = p.possible_values.index("LOWBAT")
        # p._set_value(val)
        # assert d.is_battery_low == True
        # p._set_value(0)
        # assert d.is_battery_low == False


    # def test_battery_state(self, d):
        # assert type(d.battery_state) == ParameterFLOAT
        # assert d.battery_state.unit == "V"



# class TestHM_PBI_4_FM(lib.TestCCUClassWideCCU2):
    # @pytest.fixture(scope="class")
    # def d(self, ccu2):
        # return list(ccu2.devices.query(device_name="Büro-Schalter"))[0]


    # def test_switches(self, d):
        # for num in range(1, 5):
            # switch = getattr(d, "switch%d" % num)
            # assert isinstance(switch, ChannelKey)



def test_device_class_list():
    assert len(device_classes_by_type_name) > 0
    assert "Device" not in device_classes_by_type_name
    assert "SpecificDevice" not in device_classes_by_type_name
    assert "HM-ES-PMSw1-Pl" in device_classes_by_type_name
    assert device_classes_by_type_name["HM-ES-PMSw1-Pl"] == HM_ES_PMSw1_Pl


def test_channel_class_list():
    assert len(channel_classes_by_type_name) > 0
    assert "Channel" not in channel_classes_by_type_name
    assert "CLIMATECONTROL_REGULATOR" in channel_classes_by_type_name
    assert channel_classes_by_type_name["CLIMATECONTROL_REGULATOR"] == ChannelClimaRegulator
