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

import pytest
from tomlguard.error import TomlAccessError
from tomlguard._base import GuardBase
from tomlguard.tomlguard import TomlGuard
from tomlguard.proxies.failure import TomlGuardFailureProxy

logging = logmod.root

class TestProxiedTomlGuard:

    def test_initial(self):
        base = TomlGuard({"test": "blah"})
        proxied = base.on_fail("aweg")
        assert(isinstance(proxied, TomlGuardFailureProxy))
        assert(isinstance(proxied.doesnt_exist, TomlGuardFailureProxy))

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
        assert(isinstance(proxied, TomlGuardFailureProxy))
        assert(proxied() == "blah")

    def test_proxy_nested_value_retrieval(self):
        base     = TomlGuard({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test.blah.bloo
        assert(isinstance(proxied, TomlGuardFailureProxy))
        assert(proxied() == "final")

    def test_proxy_none_value_use_fallback(self):
        base    = TomlGuard({"test": None})
        assert(base.test is None)
        proxied = base.on_fail("aweg").test
        assert(base.test is None)
        assert(isinstance(proxied, TomlGuardFailureProxy))
        assert(base.test is None)
        assert(proxied._fallback == "aweg")
        assert(proxied() == "aweg")

    def test_proxy_nested_false_value_uses_fallback(self):
        base     = TomlGuard({"top": {"mid": {"bot": None}}})
        proxied = base.on_fail("aweg").top.mid.bot
        assert(isinstance(proxied, TomlGuardFailureProxy))
        assert(proxied() is "aweg")

    def test_proxy_fallback(self):
        base     = TomlGuard({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test.blah.missing
        assert(isinstance(proxied, TomlGuardFailureProxy))
        assert(proxied() == "aweg")

    def test_no_proxy_error(self):
        base     = TomlGuard({"test": { "blah": {"bloo": "final"}}})
        with pytest.raises(TomlAccessError):
            base.test.blah()

    def test_proxy_early_check(self):
        base     = TomlGuard({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test
        assert(isinstance(proxied, TomlGuardFailureProxy))

    def test_proxy_multi_use(self):
        base     = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        proxied = base.on_fail("aweg").test.blah
        assert(proxied.bloo() == "final")
        assert(proxied.aweg() == "joijo")

