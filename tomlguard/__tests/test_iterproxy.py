#!/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import logging as logmod
import warnings
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple,
                    TypeVar, cast)
##-- end imports
logging = logmod.root

import pytest
from tomlguard.error import TomlAccessError
from tomlguard.utils.iter_proxy import TomlGuardIterProxy

class TestIterProxy:

    def test_initial(self):
        basic = TomlGuardIterProxy(None, fallback=[5])
        assert(isinstance(basic, TomlGuardIterProxy))

    def test_fail_on_noniterable_value(self):
        with pytest.raises(TypeError):
            TomlGuardIterProxy(None, fallback=5)

    def test_fail_on_bad_kind(self):
        with pytest.raises(TypeError):
            TomlGuardIterProxy(None, fallback=[5], kind="bad")

    def test_default_list_value(self):
        basic = TomlGuardIterProxy(None)
        assert(basic._fallback == None)

    def test_repr(self):
        basic = TomlGuardIterProxy(None, fallback=[5]).blah.bloo
        assert(repr(basic) == "<TomlGuardIterProxy.first: <root>:blah.bloo ([5]) <typing.Any> >")

    def test_repr_preindex(self):
        basic = TomlGuardIterProxy([5], index=["blah", "bloo"]).sub.test
        assert(repr(basic) == "<TomlGuardIterProxy.first: blah.bloo:sub.test (None) <typing.Any> >")

    def test_attr(self):
        basic = TomlGuardIterProxy([5], index=["blah", "bloo"]).sub.test
        assert(basic._subindex() == ["sub", "test"])
        assert(basic._index() == ["blah", "bloo"])

    def test_item_updates_subindex(self):
        basic = TomlGuardIterProxy([5], index=["blah", "bloo"])['sub']['test']
        assert(basic._subindex() == ["sub", "test"])
        assert(basic._index() == ["blah", "bloo"])

    def test_multi_item(self):
        basic = TomlGuardIterProxy([5], index=["blah", "bloo"])['sub', 'test']
        assert(basic._subindex() == ["sub", "test"])
        assert(basic._index() == ["blah", "bloo"])

    def test_get_first(self):
        basic = TomlGuardIterProxy([[5], [10]], kind="first")
        assert(basic() == 5)

    def test_get_first_more(self):
        basic = TomlGuardIterProxy([[5, 2, 1,5], [10, 1,2,54]], kind="first")
        assert(basic() == 5)

    def test_call_first_non_empty(self):
        basic = TomlGuardIterProxy([[], [10]], kind="first")
        assert(basic() == 10)

    def test_call_first_fallback(self):
        basic = TomlGuardIterProxy([[], []], fallback=[2], kind="first")
        assert(basic() == [2])

    def test_call_first_no_fallback(self):
        basic = TomlGuardIterProxy([[], []], kind="first", fallback=(None,))
        with pytest.raises(TomlAccessError):
            basic()

    def test_call_all_requires_nested(self):
        basic = TomlGuardIterProxy([5, 10, 15], kind="all")
        with pytest.raises(TypeError):
            basic()

    def test_call_all_lists(self):
        basic = TomlGuardIterProxy([[5, 10, 15], ["a","b","c"]], kind="all")
        assert(basic() == [5, 10, 15, "a","b","c"])

    def test_call_all_empty_list(self):
        basic = TomlGuardIterProxy([], kind="all", fallback=(None,))
        with pytest.raises(TomlAccessError):
            basic()

    def test_call_all_allow_empty_list(self):
        basic = TomlGuardIterProxy([], kind="all", fallback=[])
        assert(basic() == [])

    def test_call_all_allow_None(self):
        basic = TomlGuardIterProxy([], kind="all", fallback=None)
        assert(basic() is None)

    def test_basic_flat_dict_allow_None(self):
        basic = TomlGuardIterProxy([], kind="flat", fallback=None)
        assert(basic() is None)

    def test_basic_flat_dict_simple(self):
        basic = TomlGuardIterProxy([{"a":2}, {"b": 5}], kind="flat", fallback=(None,))
        assert(basic() == {"a":2, "b": 5})

    def test_basic_flat_list_fail(self):
        basic = TomlGuardIterProxy([[1,2,3], [4,5,6]], kind="flat")
        with pytest.raises(TypeError):
            basic()
