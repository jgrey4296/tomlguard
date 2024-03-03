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
from tomlguard.utils.proxy import TomlGuardProxy

class TestProxy:

    def test_initial(self):
        proxy = TomlGuardProxy(None, fallback=2)
        assert(isinstance(proxy, TomlGuardProxy))

    def test_attr(self):
        proxy = TomlGuardProxy(None, fallback=2)
        accessed = proxy.blah.bloo
        assert(repr(accessed) == "<TomlGuardProxy: <root>.blah.bloo:Any>")
        assert(repr(proxy) == "<TomlGuardProxy: <root>:Any>")

    def test_item(self):
        proxy    = TomlGuardProxy(None, fallback=2)
        accessed = proxy['blah']['bloo']
        assert(repr(accessed) == "<TomlGuardProxy: <root>.blah.bloo:Any>")
        assert(repr(proxy) == "<TomlGuardProxy: <root>:Any>")

    def test_multi_item(self):
        proxy    = TomlGuardProxy(None, fallback=2)
        accessed = proxy['blah', 'bloo']
        assert(repr(proxy) == "<TomlGuardProxy: <root>:Any>")
        assert(repr(accessed) == "<TomlGuardProxy: <root>.blah.bloo:Any>")

    def test_multi_item_expansion(self):
        proxy       = TomlGuardProxy(None, fallback=2)
        access_list = ["blah", "bloo"]
        accessed = proxy["blah", "bloo"]
        assert(repr(accessed) == "<TomlGuardProxy: <root>.blah.bloo:Any>")

    @pytest.mark.skip(reason="FIXME")
    def test_multi_item_star_expansion(self):
        # only for py3.11+?
        proxy       = TomlGuardProxy(None, fallback=2)
        access_list = ["blah", "bloo"]
        # accessed    = proxy[*access_list]
        accessed = []
        assert(repr(accessed) == "<TomlGuardProxy: <root>.blah.bloo:Any>")

    def test_call_get_value(self):
        proxy = TomlGuardProxy(5, fallback=2)
        assert(proxy() == 5)

    def test_call_get_None_value(self):
        proxy = TomlGuardProxy(None, fallback=None)
        assert(proxy() == None)

    def test_call_get_fallback(self):
        proxy = TomlGuardProxy(None, fallback=2)
        assert(proxy() == 2)

    def test_call_fallback_wrapper(self):
        proxy = TomlGuardProxy(None, fallback=2)
        assert(proxy(fallback_wrapper=lambda x: x*2) == 4)

    def test_wrapper(self):
        proxy = TomlGuardProxy(3, fallback=2)
        assert(proxy(wrapper=lambda x: x*2) == 6)

    def test_call_fallback_wrapper_error(self):

        def bad_wrapper(val):
            raise TypeError()

        proxy = TomlGuardProxy(None, fallback=2)
        with pytest.raises(TypeError):
            proxy(fallback_wrapper=bad_wrapper)

    def test_call_wrapper_error(self):

        def bad_wrapper(val):
            raise TypeError()

        proxy = TomlGuardProxy(3, fallback=2)
        with pytest.raises(TypeError):
            proxy(wrapper=bad_wrapper)

    def test_types(self):
        proxy = TomlGuardProxy(True, fallback=2, types=int)
        assert(proxy is not None)

    def test_types_fail(self):
        with pytest.raises(TypeError):
            TomlGuardProxy(None, fallback="blah", types=int)

    def test_proxy_inject(self):
        proxy1 = TomlGuardProxy(None, fallback=2, types=int)
        proxy2 = proxy1._inject(5)
        assert(proxy2() == 5)

    def test_proxy_value_retrieval_typecheck_fail(self):
        proxy1 = TomlGuardProxy(None, fallback=2, types=int)
        with pytest.raises(TypeError):
            proxy1._inject("blah")()

    def test_proxy_inject_index_update(self):
        proxy1 = TomlGuardProxy(None, fallback=2, types=int).blah.bloo
        proxy2 = proxy1._inject(5).awef
        assert(proxy1._index() == ["<root>", "blah", "bloo"])
        assert(proxy2._index() == ["<root>", "blah", "bloo", "awef"])
        assert(proxy2() == 5)
