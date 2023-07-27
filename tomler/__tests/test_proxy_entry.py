#!/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import logging as logmod
import warnings
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
##-- end imports
logging = logmod.root

import pytest
from tomler.error import TomlAccessError
from tomler.base import TomlerBase
from tomler.tomler import Tomler
from tomler.utils.proxy import TomlerProxy
from tomler.utils.iter_proxy import TomlerIterProxy

class TestProxiedTomler:

    def test_initial(self):
        base = Tomler({"test": "blah"})
        proxied = base.on_fail("aweg")
        assert(isinstance(proxied, TomlerProxy))
        assert(isinstance(proxied.doesnt_exist, TomlerProxy))

    def test_proxy_on_existing_key(self):
        base = Tomler({"test": "blah"})
        proxied = base.on_fail("aweg")
        assert("blah" == proxied.test())

    def test_proxy_on_bad_key(self):
        base    = Tomler({"test": "blah"})
        proxied = base.on_fail("aweg")
        assert("aweg" == proxied.awehjo())

    def test_proxy_index_independence(self):
        base    = Tomler({"test": "blah"})
        base_val = base.test
        proxied = base.on_fail("aweg")
        good_key = proxied.test
        bad_key = proxied.ajojo

        assert(base._index() == ["<root>"])
        assert(proxied._index() == ["<root>"])
        assert(good_key._index() == ["<root>", "test"])
        assert(bad_key._index() == ["<root>", "ajojo"])

    def test_proxy_multi_independence(self):
        base     = Tomler({"test": "blah"})
        proxied  = base.on_fail("aweg")
        proxied2 = base.on_fail("jioji")
        assert(proxied is not proxied2)
        assert("aweg" == proxied.awehjo())
        assert("jioji" == proxied2.awjioq())

    def test_proxy_value_retrieval(self):
        base     = Tomler({"test": "blah"})
        proxied = base.on_fail("aweg").test
        assert(isinstance(proxied, TomlerProxy))
        assert(proxied() == "blah")

    def test_proxy_nested_value_retrieval(self):
        base     = Tomler({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test.blah.bloo
        assert(isinstance(proxied, TomlerProxy))
        assert(proxied() == "final")

    def test_proxy_false_value_retrieval(self):
        base    = Tomler({"test": None})
        assert(base.test is None)
        proxied = base.on_fail("aweg").test
        assert(base.test is None)
        assert(isinstance(proxied, TomlerProxy))
        assert(base.test is None)
        assert(proxied._fallback == "aweg")
        assert(proxied() == None)

    def test_proxy_nested_false_value_retrieval(self):
        base     = Tomler({"top": {"mid": {"bot": None}}})
        proxied = base.on_fail("aweg").top.mid.bot
        assert(isinstance(proxied, TomlerProxy))
        assert(proxied() is None)

    def test_proxy_fallback(self):
        base     = Tomler({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test.blah.missing
        assert(isinstance(proxied, TomlerProxy))
        assert(proxied() == "aweg")

    def test_no_proxy_error(self):
        base     = Tomler({"test": { "blah": {"bloo": "final"}}})
        with pytest.raises(TomlAccessError):
            base.test.blah()

    def test_proxy_early_check(self):
        base     = Tomler({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test
        assert(isinstance(proxied, TomlerProxy))

    def test_proxy_multi_use(self):
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        proxied = base.on_fail("aweg").test.blah
        assert(proxied.bloo() == "final")
        assert(proxied.aweg() == "joijo")

    def test_proxied_report_empty(self, mocker):
        mocker.patch.object(TomlerBase, "_defaulted", set())
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        assert(Tomler.report_defaulted() == [])

    def test_proxied_report_no_existing_values(self, mocker):
        mocker.patch.object(TomlerBase, "_defaulted", set())
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.test.blah.bloo
        base.test.blah.aweg
        assert(Tomler.report_defaulted() == [])

    def test_proxied_report_missing_values(self, mocker):
        mocker.patch.object(TomlerBase, "_defaulted", set())
        base              = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.on_fail(False).this.doesnt.exist()
        base.on_fail(False).test.blah.other()

        defaulted = Tomler.report_defaulted()
        assert("<root>.this.doesnt.exist = false # <Any>" in defaulted)
        assert("<root>.test.blah.other = false # <Any>" in defaulted)

    def test_proxied_report_missing_typed_values(self, mocker):
        mocker.patch.object(TomlerBase, "_defaulted", set())
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.on_fail("aValue", str).this.doesnt.exist()
        base.on_fail(2, int).test.blah.other()

        defaulted = Tomler.report_defaulted()
        assert("<root>.this.doesnt.exist = 'aValue' # <str>" in defaulted)
        assert("<root>.test.blah.other = 2 # <int>" in defaulted)

    @pytest.mark.skip("not implemented")
    def test_proxied_report_no_duplicates(self):
        raise NotImplementedError()

    def test_proxied_flatten(self):
        base  = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        proxy = base.flatten_on({})
        assert(isinstance(proxy, TomlerIterProxy))

    def test_proxied_flatten_call(self):
        base   = Tomler({"test": { "blah": [{"bloo": "final", "aweg": "joijo"}, {"other": 5}]}})
        result = base.flatten_on({}).test.blah()
        assert(dict(result) == {"bloo": "final", "aweg": "joijo", "other": 5})

    def test_proxied_flatten_fallback(self):
        base   = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        result = base.flatten_on({}).test.blah()
        assert(isinstance(result, dict))

    def test_proxied_flatten_fallback_valued(self):
        base   = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        result = base.flatten_on({"a": "test"}).test.blah()
        assert(result == {"a": "test"})

    def test_proxied_bad_fallback(self):
        base   = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        with pytest.raises(TypeError):
            base.flatten_on(2)

