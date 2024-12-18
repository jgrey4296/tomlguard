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
from tomlguard.tomlguard import TomlGuard

class TestBaseTomlGuard:

    def test_initial(self):
        basic = TomlGuard({"test": "blah"})
        assert(basic is not None)

    def test_basic_access(self):
        basic = TomlGuard({"test": "blah"})
        assert(basic.test == "blah")

    def test_basic_item_access(self):
        basic = TomlGuard({"test": "blah"})
        assert(basic['test'] == "blah")

    def test_multi_item_access(self):
        basic = TomlGuard({"test": {"blah": "bloo"}})
        assert(basic['test', "blah"] ==  "bloo")

    def test_basic_access_error(self):
        basic = TomlGuard({"test": "blah"})
        with pytest.raises(TomlAccessError):
            basic.none_existing

    def test_item_access_error(self):
        basic = TomlGuard({"test": "blah"})
        with pytest.raises(TomlAccessError):
            basic['non_existing']

    def test_dot_access(self):
        basic = TomlGuard({"test": "blah"})
        assert(basic.test == "blah")

    def test_index(self):
        basic = TomlGuard({"test": "blah"})
        assert(basic._index() == ["<root>"])

    def test_index_independence(self):
        basic = TomlGuard({"test": "blah"})
        assert(basic._index() == ["<root>"])
        basic.test
        assert(basic._index() == ["<root>"])

    def test_nested_access(self):
        basic = TomlGuard({"test": {"blah": 2}})
        assert(basic.test.blah == 2)

    def test_repr(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        assert(repr(basic) == "<TomlGuard:['test', 'bloo']>")

    def test_immutable(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        with pytest.raises(TypeError):
            basic.test = 5

    def test_uncallable(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        with pytest.raises(TomlAccessError):
            basic()

    def test_iter(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        pairs = list(basic)
        assert(pairs == [("test", {"blah":2}), ("bloo", 2)])

    def test_contains(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        assert("test" in basic)

    def test_contains_fail(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        assert("blah" not in basic)

    def test_get(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        assert(basic.get("bloo") == 2)

    def test_get_default(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        assert(basic.get("blah") is None)

    def test_get_default_value(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        assert(basic.get("blah", 5) == 5)

    def test_keys(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        assert(list(basic.keys()) == ["test", "bloo"])

    def test_items(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        assert(list(basic.items()) == [("test", {"blah": 2}), ("bloo", 2)])

    def test_values(self):
        basic = TomlGuard({"test": {"blah": 2}, "bloo": 2})
        assert(list(basic.values()) == [{"blah": 2}, 2])

    def test_list_access(self):
        basic = TomlGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert(basic.test.blah == [1,2,3])
        assert(basic.bloo == ["a","b","c"])

    def test_contains(self):
        basic = TomlGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert("test" in basic)

    def test_contains_false(self):
        basic = TomlGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert("doesntexist" not in basic)

    def test_contains_nested_but_doesnt_recurse(self):
        basic = TomlGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert("blah" not in basic)

    def test_contains_nested(self):
        basic = TomlGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert("blah" in basic.test)

    def test_contains_nested_false(self):
        basic = TomlGuard({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        assert("doesntexist" not in basic.test)


class TestLoaderTomlGuard:

    @pytest.mark.skip(reason="not implemented")
    def test_initial_load(self):
        # TODO
        raise

class TestTomlGuardMerge:

    def test_initial(self):
        simple = TomlGuard.merge({"a":2}, {"b": 5})
        assert(isinstance(simple, TomlGuard))
        assert(simple._table() == {"a": 2, "b": 5})

    def test_merge_conflict(self):
        with pytest.raises(KeyError):
            TomlGuard.merge({"a":2}, {"a": 5})

    def test_merge_with_shadowing(self):
        basic = TomlGuard.merge({"a":2}, {"a": 5, "b": 5}, shadow=True)
        assert(dict(basic) == {"a":2, "b": 5})


    def test_merge_tomlguards(self):
        first  = TomlGuard({"a":2})
        second = TomlGuard({"a": 5, "b": 5})

        merged = TomlGuard.merge(first ,second, shadow=True)
        assert(dict(merged) == {"a":2, "b": 5})


class TestFailAccess:

    def test_basic(self):
        obj = TomlGuard({})
        assert(obj is not  None)

    def test_basic_fail(self):
        obj = TomlGuard({})
        result = obj.on_fail(5).nothing()
        assert(result == 5)


    def test_fail_access_dict(self):
        obj = TomlGuard({"nothing": {}})
        result = obj.on_fail({}).nothing['blah']()
        assert(isinstance(result, dict))


    def test_fail_access_list(self):
        obj = TomlGuard({"nothing": []})
        result = obj.on_fail([]).nothing[1]()
        assert(isinstance(result, list))


    def test_fail_access_type_mismatch(self):
        obj = TomlGuard({"nothing": {}})
        result = obj.on_fail({}).nothing[1]()
        assert(isinstance(result, dict))
