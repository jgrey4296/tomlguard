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
from tomlguard import TomlGuard


class TestIterFirstProxyUse:

    def test_basic(self):
        obj = TomlGuard({"top":{"mid":{"low":[1,2,3]}}})
        assert(isinstance(obj, TomlGuard))


    def test_basic_access(self):
        obj   = TomlGuard({"top":{"mid":{"low":[1,2,3]}}})
        proxy = obj.first_of([11]).top.mid.low
        assert(isinstance(proxy, TomlGuardIterProxy))


    def test_basic_reify(self):
        obj   = TomlGuard({"top":{"mid":{"low":[1,2,3]}}})
        proxy = obj.first_of([11]).top.mid.low()
        assert(proxy == [1,2,3])


    def test_nested_access(self):
        obj   = TomlGuard({"top":{"mid":[
            {"val": {"subval": [1,2,3]}},
            {"val": {"subval": [12,13,14]}},
    ]}})
        proxy = obj.first_of([11]).top.mid.val.subval
        assert(proxy() == [1,2,3])


    def test_nested_partial_access(self):
        obj   = TomlGuard({"top":{"mid":[
            {"val": {"notsubval": [1,2,3]}},
            {"val": {"subval": [12,13,14]}},
    ]}})
        proxy = obj.first_of([11]).top.mid.val.subval
        assert(proxy() == [12,13,14])


    def test_nested_partial_access_missing_parent(self):
        obj   = TomlGuard({"top":{"mid":[
            {"notval": {"subval": [1,2,3]}},
            {"val": {"subval": [12,13,14]}},
    ]}})
        proxy = obj.first_of([11]).top.mid.val.subval
        assert(proxy() == [12,13,14])


    def test_nested_access_fallback(self):
        obj   = TomlGuard({"top":{"mid":[
            {"notval": {"subval": [1,2,3]}},
            {"badval": {"subval": [12,13,14]}},
    ]}})
        proxy = obj.first_of([11]).top.mid.val.subval
        assert(proxy() == [11])


    def test_access_no_fallback(self):
        obj   = TomlGuard({"top":{"mid":[
            {"notval": {"subval": [1,2,3]}},
            {"badval": {"subval": [12,13,14]}},
    ]}})
        proxy = obj.first_of(None).top.mid.val.subval
        assert(proxy() == None)


class TestIterFirstProxyUse:

    def test_basic(self):
        obj = TomlGuard({"top":{"mid":{"low":[1,2,3]}}})
        assert(isinstance(obj, TomlGuard))


    def test_basic_access(self):
        obj   = TomlGuard({"top":{"mid":{"low":[1,2,3]}}})
        proxy = obj.first_of([11]).top.mid.low
        assert(isinstance(proxy, TomlGuardIterProxy))


    def test_basic_reify(self):
        obj   = TomlGuard({"top":{"mid":{"low":[1,2,3]}}})
        proxy = obj.first_of([11]).top.mid.low()
        assert(proxy == [1,2,3])


    def test_nested_access(self):
        obj   = TomlGuard({"top":{"mid":[
            {"val": {"subval": [1,2,3]}},
            {"val": {"subval": [12,13,14]}},
    ]}})
        proxy = obj.first_of([11]).top.mid.val.subval
        assert(proxy() == [1,2,3])


    def test_nested_partial_access(self):
        obj   = TomlGuard({"top":{"mid":[
            {"val": {"notsubval": [1,2,3]}},
            {"val": {"subval": [12,13,14]}},
    ]}})
        proxy = obj.first_of([11]).top.mid.val.subval
        assert(proxy() == [12,13,14])


    def test_nested_partial_access_missing_parent(self):
        obj   = TomlGuard({"top":{"mid":[
            {"notval": {"subval": [1,2,3]}},
            {"val": {"subval": [12,13,14]}},
    ]}})
        proxy = obj.first_of([11]).top.mid.val.subval
        assert(proxy() == [12,13,14])


    def test_nested_access_fallback(self):
        obj   = TomlGuard({"top":{"mid":[
            {"notval": {"subval": [1,2,3]}},
            {"badval": {"subval": [12,13,14]}},
    ]}})
        proxy = obj.first_of([11]).top.mid.val.subval
        assert(proxy() == [11])


    def test_wrapper(self):
        obj   = TomlGuard({"top":{"mid":[
            {"notval": {"subval": [1,2,3]}},
            {"val": {"subval": [12,13,14]}},
        ]}})
        proxy = obj.first_of(None).top.mid.val.subval
        assert(proxy(wrapper=lambda x: [y+2 for y in x]) == [14,15,16])


    def test_fallback_wrapper(self):
        obj   = TomlGuard({"top":{"mid":[
            {"notval": {"subval": [1,2,3]}},
            {"badval": {"subval": [12,13,14]}},
        ]}})
        proxy = obj.first_of([1,2,3]).top.mid.val.subval
        assert(proxy(fallback_wrapper=lambda x: [y+2 for y in x]) == [3,4,5])
