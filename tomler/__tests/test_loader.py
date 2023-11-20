#!/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple,
                    TypeVar, cast)
import warnings

##-- end imports

import pytest
from tomler.tomler import Tomler

logging = logmod.root

data_dir = pl.Path(__file__).parent / "__data"

class TestTomlerLoader:

    @pytest.fixture(scope="function")
    def setup(self):
        pass

    @pytest.fixture(scope="function")
    def cleanup(self):
        yield
        pass

    def test_initial(self):
        data_str = (data_dir / "data.toml").read_text()
        assert(bool(data_str))
        simple = Tomler.read(data_str)
        assert(bool(simple))

    def test_content(self):
        data_str = (data_dir / "data.toml").read_text()
        assert(bool(data_str))
        simple = Tomler.read(data_str)
        assert("basic" in simple)
        assert("value" in simple)

    def test_from_dict(self):
        simple = Tomler.from_dict({"val": 5, "other": "blah", "nested": {"val": True}})
        assert("val" in simple)
        assert("other" in simple)
        assert(simple.nested.val is True)

    def test_load(self):
        simple = Tomler.load(data_dir / "data.toml")
        assert("basic" in simple)
        assert(simple.basic == "test")

    def test_load_dir(self):
        simple = Tomler.load_dir(data_dir)
        assert("basic" in simple)
        assert("a-different-val" in simple)
        assert(simple.a_different_val == "blah")
        assert(simple.basic == "test")
