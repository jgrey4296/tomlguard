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
from tomler.utils.proxy import TomlerProxy

class TestProxy:
    def test_initial(self):
        proxy = TomlerProxy(None, fallback=2)
        assert(isinstance(proxy, TomlerProxy))

    def test_attr(self):
        proxy = TomlerProxy(None, fallback=2)
        accessed = proxy.blah.bloo
        assert(repr(accessed) == "<TomlerProxy: <root>.blah.bloo:Any>")
        assert(repr(proxy) == "<TomlerProxy: <root>:Any>")

    def test_item(self):
        proxy    = TomlerProxy(None, fallback=2)
        accessed = proxy['blah']['bloo']
        assert(repr(accessed) == "<TomlerProxy: <root>.blah.bloo:Any>")
        assert(repr(proxy) == "<TomlerProxy: <root>:Any>")


    def test_multi_item(self):
        proxy    = TomlerProxy(None, fallback=2)
        accessed = proxy['blah', 'bloo']
        assert(repr(proxy) == "<TomlerProxy: <root>:Any>")
        assert(repr(accessed) == "<TomlerProxy: <root>.blah.bloo:Any>")

    def test_multi_item_expansion(self):
        proxy       = TomlerProxy(None, fallback=2)
        access_list = ["blah", "bloo"]
        accessed    = proxy[*access_list]
        assert(repr(accessed) == "<TomlerProxy: <root>.blah.bloo:Any>")

    def test_call_get_value(self):
        proxy = TomlerProxy(5, fallback=2)
        assert(proxy() == 5)

    def test_call_get_None_value(self):
        proxy = TomlerProxy(None, fallback=2)
        assert(proxy() == None)

    def test_call_get_fallback(self):
        proxy = TomlerProxy((None,), fallback=2)
        assert(proxy() == 2)

    def test_call_wrapper(self):
        proxy = TomlerProxy((None,), fallback=2)
        assert(proxy(wrapper=lambda x: x*2) == 4)

    def test_call_wrapper_error(self):
        def bad_wrapper(val):
            raise TypeError()

        proxy = TomlerProxy(None, fallback=2)
        with pytest.raises(TypeError):
            proxy(wrapper=bad_wrapper)

    def test_types(self):
        proxy = TomlerProxy(True, fallback=2, types=int)
        assert(proxy is not None)

    def test_types_fail(self):
        with pytest.raises(TypeError):
            TomlerProxy(None, fallback="blah", types=int)

    def test_proxy_inject(self):
        proxy1 = TomlerProxy(None, fallback=2, types=int)
        proxy2 = proxy1._inject(5)
        assert(proxy2() == 5)

    def test_proxy_value_retrieval_typecheck_fail(self):
        proxy1 = TomlerProxy(None, fallback=2, types=int)
        with pytest.raises(TypeError):
            proxy1._inject("blah")()

    def test_proxy_inject_index_update(self):
        proxy1 = TomlerProxy(None, fallback=2, types=int).blah.bloo
        proxy2 = proxy1._inject(5).awef
        assert(proxy1._index() == ["<root>", "blah", "bloo"])
        assert(proxy2._index() == ["<root>", "blah", "bloo", "awef"])
        assert(proxy2() == 5)


