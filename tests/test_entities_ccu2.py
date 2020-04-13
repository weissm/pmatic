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

import pmatic
import pmatic.utils as utils
import lib
from pmatic.entities import Device, \
                            Channel,  \
                            ChannelShutterContact, \
                            ChannelKey 
from pmatic.params import ParameterFLOAT, ParameterACTION, ParameterBOOL, ParameterINTEGER

from pmatic.exceptions import PMException





class TestHM_CC_RT_DN(lib.TestCCUClassWideCCU2):
    @pytest.fixture(scope="class")
    def d(self, ccu2):
        return list(ccu2.devices.query(device_name="Wohnzimmer"))[0]


    def test_temperature(self, d):
        assert type(d.temperature) == ParameterFLOAT
        assert isinstance(d.temperature.value, float)
        assert utils.is_string("%s" % d.temperature)


    def test_set_temperature(self, d):
        assert type(d.set_temperature) == ParameterFLOAT
        assert isinstance(d.set_temperature.value, float)
        assert utils.is_string("%s" % d.set_temperature)


    def test_is_off(self, d):
        assert d.set_temperature._set_value(10.5)
        assert d.is_off == False
        assert d.set_temperature._set_value(4.5)
        assert d.is_off == True


    def test_change_temperature(self, d):
        prev_temp = d.set_temperature.value

        d.set_temperature = 9.5
        assert d.set_temperature == 9.5

        d.set_temperature_comfort()
        # if not lib.is_testing_with_real_ccu():
        d.set_temperature._value = 20.0
        assert d.set_temperature != 9.5

        d.set_temperature = 9.5

        d.set_temperature_lowering()
        # if not lib.is_testing_with_real_ccu():
        d.set_temperature._value = 10.0
        assert d.set_temperature != 9.5

        d.set_temperature = prev_temp


    def test_turn_off(self, d):
        prev_temp = d.set_temperature.value

        d.turn_off()
        assert d.is_off == True

        d.set_temperature = prev_temp


    def test_control_mode(self, d, monkeypatch):
        # Test setting invalid control mode
        with pytest.raises(PMException) as e:
            d.control_mode = "BIMBAM"
        assert "must be one of" in str(e)

        def set_mode(mode):
            d.control_mode = mode

            # Fake the value for testing without CCU. When testing with CCU, this
            # value is fetched fresh from the CCU.
#            if not lib.is_testing_with_real_ccu():
            d.control_mode._value = mode

            if mode == "BOOST":
                d.boost_duration._value = 5

            # In my tests it took some time to apply the new mode. Wait for 10 seconds
            # maximum after setting the new mode.
            for i in range(20):
                if d.control_mode == mode:
                    break
                time.sleep(1)

            assert d.control_mode == mode

        # When testing without CCU the values must not be refetched because
        # the API calls for reading the values are always using the same parameter
        # set, but should return different states. This is currently not supported
        # by the recorded CCU transaction mechanism.
        # if not lib.is_testing_with_real_ccu():
        monkeypatch.setattr(d.channels[4], "_value_update_needed", lambda: False)

        # Ensure consistent initial state
        set_mode("AUTO")
        d.set_temperature = 20.0

        prev_temp = d.set_temperature.value
        set_mode("MANUAL")

        assert d.set_temperature.value == prev_temp

        d.turn_off()
        assert d.is_off == True

        set_mode("MANUAL")
        assert d.set_temperature.value == d.set_temperature.default

        assert d.boost_duration == None
        set_mode("BOOST")

        assert type(d.boost_duration) == ParameterINTEGER
        assert d.boost_duration < 6

        # FIXME: TEst party mode
        set_mode("AUTO")


    def test_is_battery_low(self, d):
        assert d.is_battery_low == False
        p = d.channels[4].values["FAULT_REPORTING"]
        val = p.possible_values.index("LOWBAT")
        p._set_value(val)
        assert d.is_battery_low == True
        p._set_value(0)
        assert d.is_battery_low == False


    def test_battery_state(self, d):
        assert type(d.battery_state) == ParameterFLOAT
        assert d.battery_state.unit == "V"


class TestHM_PBI_4_FM(lib.TestCCUClassWideCCU2):
    @pytest.fixture(scope="class")
    def d(self, ccu2):
        return list(ccu2.devices.query(device_name="Büro-Schalter"))[0]


    def test_switches(self, d):
        for num in range(1, 5):
            switch = getattr(d, "switch%d" % num)
            assert isinstance(switch, ChannelKey)


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

