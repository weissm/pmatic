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

try:
    from _pytest.monkeypatch import MonkeyPatch as monkeypatch
except ImportError:
    from _pytest.monkeypatch import monkeypatch

#try:
#    from builtins import object # pylint:disable=redefined-builtin
#except ImportError:
#    pass

# try:
    # # Python 2.x
    # import __builtin__ as builtins
# except ImportError:
    # # Python 3+
    # import builtins

import re
import os
import json
from hashlib import sha256

try:
    from StringIO import StringIO
except ImportError:
    # and for python 3
    from io import BytesIO as StringIO

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, Request
    from urllib2 import HTTPError


import pmatic
import pmatic.api
import pmatic.utils as utils

resources_path = "tests/resources"


def request_id(data):
    try:
        req = json.loads(data.decode("utf-8"))
        method = req["method"]
    except ValueError:
        # CCU API has always JSON, but pushover notify has urlencoded data
        method = "urlopen"

    data_hash = sha256(data).hexdigest()

    return "%s_%s" % (method, data_hash)


def response_file_path(request_id, __target__ = ""):
    return "%s/%s/%s.response" % (resources_path, __target__, request_id)


def status_file_path(request_id, __target__ = ""):
    return "%s/%s/%s.status" % (resources_path, __target__, request_id)


def data_file_path(request_id, __target__ = ""):
    return "%s/%s/%s.data" % (resources_path, __target__, request_id)


def fake_urlopen_ccu2(url_or_request, data=None, timeout=None):
    return fake_urlopen(url_or_request, data=None, timeout=None, __target__="ccu2")

def fake_urlopen(url_or_request, data=None, timeout=None, __target__=""):
    """A stub urlopen() implementation that loads json responses from the filesystem.

    It first strips off the host part of the url and then uses the path info
    together with the post data to find a matching response. If no response has
    been recorded before, it raises an Exception() about the missing file.
    """
    if isinstance(url_or_request, Request):
        data = url_or_request.data
#        print("fake_urlopen_ccu2 with url ", url_or_request.data)

    fake_data = fake_session_id(data, data)

    # Fix the key order to get the correct hash. When json can not be
    # decoded, use the original string.
    try:
        fake_data = json.dumps(json.loads(fake_data.decode("utf-8")),
                                      sort_keys=True).encode("utf-8")
    except ValueError:
        pass

    rid = request_id(fake_data)
    response = open(response_file_path(rid, __target__ = __target__), "rb").read()
#    except:
 #       import traceback
 #       traceback.print_exc()
    http_status = int(open(status_file_path(rid, __target__ = __target__), "rb").read())

    obj = StringIO(response)
    obj.getcode = lambda: http_status

    return obj

def fake_session_id(data_byte_str, byte_str):
    new_str = re.sub(b'"_session_id_": "[0-9A-Za-z]{10}"',
                     b'"_session_id_": "xxxxxxxxxx"', byte_str)
    if b"Sessian.login" in data_byte_str:
        # Session.login returns the session id as result. Replace it here.
        return re.sub(b'"result": "[0-9A-Za-z]{10}"', b'"result": "xxxxxxxxxx"', new_str)
    else:
        return new_str


def wrap_urlopen(url_or_request, data=None, timeout=None):
    """Wraps urlopen to record the response when communicating with a real CCU."""
    if isinstance(url_or_request, Request):
        data = url_or_request.data
        url = url_or_request.get_full_url()
    assert utils.is_byte_string(data)

    try:
        obj = urlopen(url, data=data, timeout=timeout)
        response = obj.read()
        http_status = obj.getcode()
    except HTTPError as e:
        response = e.reason.encode("utf-8")
        http_status = e.code

    assert utils.is_byte_string(response)

    if not os.path.exists(resources_path):
        os.makedirs(resources_path)

    # FIXME: The ccu is performing wrong encoding at least for output of
    # executed rega scripts. But maybe this is a generic problem. Let's see
    # and only fix the known issues for the moment.
    if b"ReGa.runScript" in data or b"Interface.getParamsetDescription" in data:
        response = pmatic.api.AbstractAPI._replace_wrong_encoded_json(
                                response.decode("utf-8")).encode("utf-8")

    # Fake the session id to a fixed one for offline testing. This is needed
    # to make the recorded data change less frequently.
    fake_data = fake_session_id(data, data)
    fake_response = fake_session_id(data, response)

    # Ensure normalized sorting of keys.
    # For hashing we need a constant sorted representation of the data.
    # CCU API has always JSON, but pushover notify has urlencoded data.
    if "pushover.net" not in url:
        fake_data = json.dumps(json.loads(fake_data.decode("utf-8")),
                                      sort_keys=True).encode("utf-8")

    # When json can not be parsed, write the original response to the file
    try:
        fake_response = json.dumps(json.loads(fake_response.decode("utf-8")),
                                          sort_keys=True).encode("utf-8")
    except ValueError:
        pass

    rid = request_id(fake_data)

    open(response_file_path(rid), "wb").write(fake_response)
    open(status_file_path(rid), "wb").write(str(http_status).encode("utf-8"))
    open(data_file_path(rid), "wb").write(fake_data)

    obj = StringIO(response)
    obj.getcode = lambda: http_status
    return obj


class TestRemoteAPI(object):
    @pytest.fixture(scope="module")
    def API(self, request):
        self._monkeypatch = monkeypatch()
        if not is_testing_with_real_ccu():
            # First hook into urlopen to fake the HTTP responses
            self._monkeypatch.setattr(pmatic.api, 'urlopen', fake_urlopen)
        else:
            # When executed with real ccu we wrap urlopen for enabling recording
            self._monkeypatch.setattr(pmatic.api, 'urlopen', wrap_urlopen)

#        print ("...................... Start Remote API1")
        API = pmatic.api.RemoteAPI(
            address="http://ccu3-webui",
            credentials=("PmaticAdmin", "EPIC-SECRET-PW"),
            connect_timeout=5,
            # log_level=pmatic.DEBUG,
        )

        request.addfinalizer(API.close)

        return API

    @pytest.fixture(scope="module")
    def APICCU2(self, request):
        self._monkeypatch = monkeypatch()
        # For exisiting ccu2 responses force read from file
        self._monkeypatch.setattr(pmatic.api, 'urlopen', fake_urlopen_ccu2)
      
#        print ("........................... Start Remote API2")
        APICCU2 = pmatic.api.RemoteAPI(
            address="http://ccu3-webui",
            credentials=("Admin", "EPIC-SECRET-PW"),
            connect_timeout=5,
            target="ccu2"
            #log_level=pmatic.DEBUG,
        )
        
        request.addfinalizer(APICCU2.close)

        return APICCU2
    
class TestCCU(TestRemoteAPI):
    def _get_test_ccu(self, API):
        self._monkeypatch = monkeypatch()
        self._monkeypatch.setattr(pmatic.api, 'init', lambda: None)
                   
        ccu = pmatic.CCU()
        ccu.api = API
#        print( "ccu generation " )
        return ccu

    @pytest.fixture(scope="function")
    def ccu(self, API):
        return self._get_test_ccu(API)

class TestCCU2(TestRemoteAPI):
    def _get_test_ccu2(self, APICCU2):
        self._monkeypatch = monkeypatch()
        self._monkeypatch.setattr(pmatic.api, 'init', lambda: None)

        # # if ccu shall be reused by manager keep it for future restorage
        # if "manager_ccu" in builtins.__dict__:
            # builtinn_ccu = builtins.__dict__["manager_ccu"]
            # del builtins.__dict__["manager_ccu"]
        # else:    
            # builtinn_ccu = None
        # # if ccu shall be reused by test class check if class is instantiated and assign for reuse    
        # if "test_ccu" in builtins.__dict__:
            # try:
                # builtinn_test = builtins.__dict__["test_ccu"]
                # if builtinn_test._constructed: # check if object is really instantiated
                    # builtins.manager_ccu = builtinn_test
            # except:
                # del builtins.__dict__["test_ccu"]
                
        # ccu2 = pmatic.CCU()

        # if builtinn_ccu != None:
            # builtins.manager_ccu = builtinn_ccu
        # builtins.test_ccu = ccu2

        # print( "ccu2 has buildin " , hasattr(builtins, "test_ccu"))
        ccu2 = pmatic.CCU()
        ccu2.api = APICCU2
        return ccu2

    @pytest.fixture(scope="function")
    def ccu2(self, APICCU2):
        return self._get_test_ccu2(APICCU2)


class TestCCUClassWideCCU2(TestCCU2):
    @pytest.fixture(scope="class")
    def ccu2(self, APICCU2):
        return self._get_test_ccu2(APICCU2)

class TestCCUClassWide(TestCCU):
    @pytest.fixture(scope="class")
    def ccu(self, API):
        return self._get_test_ccu(API)


class TestCCUModuleWide(TestCCU):
    @pytest.fixture(scope="module")
    def ccu(self, API):
        return self._get_test_ccu(API)



def is_testing_with_real_ccu():
    return os.environ.get("TEST_WITH_CCU") == "1"


