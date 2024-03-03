#!/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import logging as logmod
import warnings
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeVar, cast)
##-- end imports
logging = logmod.root

import pytest
from tomlguard.error import TomlAccessError
from tomlguard.base import GuardBase
from tomlguard.tomlguard import TomlGuard
from tomlguard.utils.proxy import TomlGuardProxy
from tomlguard.utils.iter_proxy import TomlGuardIterProxy

class TestProxiedTomlGuard:

    def test_initial(self):
        base = TomlGuard({"test": "blah"})
        proxied = base.on_fail("aweg")
        assert(isinstance(proxied, TomlGuardProxy))
        assert(isinstance(proxied.doesnt_exist, TomlGuardProxy))

    def test_proxy_on_existing_key(self):
        base = TomlGuard({"test": "blah"})
        proxied = base.on_fail("aweg")
        assert("blah" == proxied.test())

    def test_proxy_on_bad_key(self):
        base    = TomlGuard({"test": "blah"})
        proxied = base.on_fail("aweg")
        assert("aweg" == proxied.awehjo())

    def test_proxy_index_independence(self):
        base    = TomlGuard({"test": "blah"})
        base_val = base.test
        proxied = base.on_fail("aweg")
        good_key = proxied.test
        bad_key = proxied.ajojo

        assert(base._index() == ["<root>"])
        assert(proxied._index() == ["<root>"])
        assert(good_key._index() == ["<root>", "test"])
        assert(bad_key._index() == ["<root>", "ajojo"])

    def test_proxy_multi_independence(self):
        base     = TomlGuard({"test": "blah"})
        proxied  = base.on_fail("aweg")
        proxied2 = base.on_fail("jioji")
        assert(proxied is not proxied2)
        assert("aweg" == proxied.awehjo())
        assert("jioji" == proxied2.awjioq())

    def test_proxy_value_retrieval(self):
        base     = TomlGuard({"test": "blah"})
        proxied = base.on_fail("aweg").test
        assert(isinstance(proxied, TomlGuardProxy))
        assert(proxied() == "blah")

    def test_proxy_nested_value_retrieval(self):
        base     = TomlGuard({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test.blah.bloo
        assert(isinstance(proxied, TomlGuardProxy))
        assert(proxied() == "final")

    def test_proxy_none_value_use_fallback(self):
        base    = TomlGuard({"test": None})
        assert(base.test is None)
        proxied = base.on_fail("aweg").test
        assert(base.test is None)
        assert(isinstance(proxied, TomlGuardProxy))
        assert(base.test is None)
        assert(proxied._fallback == "aweg")
        assert(proxied() == "aweg")

    def test_proxy_nested_false_value_uses_fallback(self):
        base     = TomlGuard({"top": {"mid": {"bot": None}}})
        proxied = base.on_fail("aweg").top.mid.bot
        assert(isinstance(proxied, TomlGuardProxy))
        assert(proxied() is "aweg")

    def test_proxy_fallback(self):
        base     = TomlGuard({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test.blah.missing
        assert(isinstance(proxied, TomlGuardProxy))
        assert(proxied() == "aweg")

    def test_no_proxy_error(self):
        base     = TomlGuard({"test": { "blah": {"bloo": "final"}}})
        with pytest.raises(TomlAccessError):
            base.test.blah()

    def test_proxy_early_check(self):
        base     = TomlGuard({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test
        assert(isinstance(proxied, TomlGuardProxy))

    def test_proxy_multi_use(self):
        base     = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        proxied = base.on_fail("aweg").test.blah
        assert(proxied.bloo() == "final")
        assert(proxied.aweg() == "joijo")

    def test_proxied_report_empty(self, mocker):
        mocker.patch.object(GuardBase, "_defaulted", set())
        base     = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        assert(TomlGuard.report_defaulted() == [])

    def test_proxied_report_no_existing_values(self, mocker):
        mocker.patch.object(GuardBase, "_defaulted", set())
        base     = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.test.blah.bloo
        base.test.blah.aweg
        assert(TomlGuard.report_defaulted() == [])

    def test_proxied_report_missing_values(self, mocker):
        mocker.patch.object(GuardBase, "_defaulted", set())
        base              = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.on_fail(False).this.doesnt.exist()
        base.on_fail(False).test.blah.other()

        defaulted = TomlGuard.report_defaulted()
        assert("<root>.this.doesnt.exist = false # <Any>" in defaulted)
        assert("<root>.test.blah.other = false # <Any>" in defaulted)

    def test_proxied_report_missing_typed_values(self, mocker):
        mocker.patch.object(GuardBase, "_defaulted", set())
        base     = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.on_fail("aValue", str).this.doesnt.exist()
        base.on_fail(2, int).test.blah.other()

        defaulted = TomlGuard.report_defaulted()
        assert("<root>.this.doesnt.exist = 'aValue' # <str>" in defaulted)
        assert("<root>.test.blah.other = 2 # <int>" in defaulted)

    @pytest.mark.skip("not implemented")
    def test_proxied_report_no_duplicates(self):
        raise NotImplementedError()

class TestProxiedIterGuards:
    @pytest.mark.xfail
    def test_proxied_flatten(self):
        base  = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        proxy = base.flatten_on({})
        assert(isinstance(proxy, TomlGuardIterProxy))

    @pytest.mark.xfail
    def test_proxied_flatten_call(self):
        base   = TomlGuard({"test": { "blah": [{"bloo": "final", "aweg": "joijo"}, {"other": 5}]}})
        result = base.flatten_on({}).test.blah()
        assert(dict(result) == {"bloo": "final", "aweg": "joijo", "other": 5})

    @pytest.mark.xfail
    def test_proxied_flatten_fallback(self):
        base   = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        result = base.flatten_on({}).test.blah()
        assert(isinstance(result, dict))

    @pytest.mark.xfail
    def test_proxied_flatten_fallback_valued(self):
        base   = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        result = base.flatten_on({"a": "test"}).test.blah()
        assert(result == {"a": "test"})

    @pytest.mark.xfail
    def test_proxied_bad_fallback(self):
        base   = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        with pytest.raises(TypeError):
            base.flatten_on(2)
