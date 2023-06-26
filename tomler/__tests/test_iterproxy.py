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
from tomler.utils.iter_proxy import TomlerIterProxy

class TestIterProxy:

    def test_initial(self):
        basic = TomlerIterProxy(None, fallback=[5])
        assert(isinstance(basic, TomlerIterProxy))

    def test_fail_on_noniterable_value(self):
        with pytest.raises(TypeError):
            TomlerIterProxy(None, fallback=5)

    def test_fail_on_bad_kind(self):
        with pytest.raises(TypeError):
            TomlerIterProxy(None, fallback=[5], kind="bad")

    def test_default_list_value(self):
        basic = TomlerIterProxy(None)
        assert(basic._fallback == None)

    def test_repr(self):
        basic = TomlerIterProxy(None, fallback=[5]).blah.bloo
        assert(repr(basic) == "<TomlerIterProxy.first: <root>:blah.bloo ([5]) <Any> >")

    def test_repr_preindex(self):
        basic = TomlerIterProxy([5], index=["blah", "bloo"]).sub.test
        assert(repr(basic) == "<TomlerIterProxy.first: blah.bloo:sub.test (None) <Any> >")

    def test_attr(self):
        basic = TomlerIterProxy([5], index=["blah", "bloo"]).sub.test
        assert(basic._subindex() == ["sub", "test"])
        assert(basic._index() == ["blah", "bloo"])

    def test_item_updates_subindex(self):
        basic = TomlerIterProxy([5], index=["blah", "bloo"])['sub']['test']
        assert(basic._subindex() == ["sub", "test"])
        assert(basic._index() == ["blah", "bloo"])

    def test_multi_item(self):
        basic = TomlerIterProxy([5], index=["blah", "bloo"])['sub', 'test']
        assert(basic._subindex() == ["sub", "test"])
        assert(basic._index() == ["blah", "bloo"])

    def test_get_first(self):
        basic = TomlerIterProxy([[5], [10]], kind="first")
        assert(basic() == 5)

    def test_get_first_more(self):
        basic = TomlerIterProxy([[5, 2, 1,5], [10, 1,2,54]], kind="first")
        assert(basic() == 5)

    def test_call_first_non_empty(self):
        basic = TomlerIterProxy([[], [10]], kind="first")
        assert(basic() == 10)

    def test_call_first_fallback(self):
        basic = TomlerIterProxy([[], []], fallback=[2], kind="first")
        assert(basic() == [2])

    def test_call_first_no_fallback(self):
        basic = TomlerIterProxy([[], []], kind="first", fallback=(None,))
        with pytest.raises(TomlAccessError):
            basic()

    def test_call_all_requires_nested(self):
        basic = TomlerIterProxy([5, 10, 15], kind="all")
        with pytest.raises(TypeError):
            basic()

    def test_call_all_lists(self):
        basic = TomlerIterProxy([[5, 10, 15], ["a","b","c"]], kind="all")
        assert(basic() == [5, 10, 15, "a","b","c"])

    def test_call_all_empty_list(self):
        basic = TomlerIterProxy([], kind="all", fallback=(None,))
        with pytest.raises(TomlAccessError):
            basic()

    def test_call_all_allow_empty_list(self):
        basic = TomlerIterProxy([], kind="all", fallback=[])
        assert(basic() == [])

    def test_call_all_allow_None(self):
        basic = TomlerIterProxy([], kind="all", fallback=None)
        assert(basic() is None)

    def test_basic_flat_dict_allow_None(self):
        basic = TomlerIterProxy([], kind="flat", fallback=None)
        assert(basic() is None)

    def test_basic_flat_dict_simple(self):
        basic = TomlerIterProxy([{"a":2}, {"b": 5}], kind="flat", fallback=(None,))
        assert(basic() == {"a":2, "b": 5})

    def test_basic_flat_list_fail(self):
        basic = TomlerIterProxy([[1,2,3], [4,5,6]], kind="flat")
        with pytest.raises(TypeError):
            basic()

