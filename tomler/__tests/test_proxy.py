#!/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import logging as logmod
import unittest
import warnings
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
from unittest import mock
##-- end imports
logging = logmod.root

##-- warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    pass
##-- end warnings

from tomler.utils.proxy import TomlerProxy

class TestProxy(unittest.TestCase):
    ##-- setup-teardown
    @classmethod
    def setUpClass(cls):
        LOGLEVEL      = logmod.DEBUG
        LOG_FILE_NAME = "log.{}".format(pl.Path(__file__).stem)

        cls.file_h        = logmod.FileHandler(LOG_FILE_NAME, mode="w")
        cls.file_h.setLevel(LOGLEVEL)

        logging.setLevel(logmod.NOTSET)
        logging.addHandler(cls.file_h)


    @classmethod
    def tearDownClass(cls):
        logging.removeHandler(cls.file_h)

    ##-- end setup-teardown

    def test_initial(self):
        proxy = TomlerProxy(None, fallback=2)
        self.assertIsInstance(proxy, TomlerProxy)

    def test_attr(self):
        proxy = TomlerProxy(None, fallback=2)
        accessed = proxy.blah.bloo
        self.assertEqual(repr(accessed), "<TomlerProxy: <root>.blah.bloo:Any>")
        self.assertEqual(repr(proxy), "<TomlerProxy: <root>:Any>")

    def test_item(self):
        proxy    = TomlerProxy(None, fallback=2)
        accessed = proxy['blah']['bloo']
        self.assertEqual(repr(accessed), "<TomlerProxy: <root>.blah.bloo:Any>")
        self.assertEqual(repr(proxy), "<TomlerProxy: <root>:Any>")


    def test_multi_item(self):
        proxy    = TomlerProxy(None, fallback=2)
        accessed = proxy['blah', 'bloo']
        self.assertEqual(repr(proxy), "<TomlerProxy: <root>:Any>")
        self.assertEqual(repr(accessed), "<TomlerProxy: <root>.blah.bloo:Any>")

    def test_multi_item_expansion(self):
        proxy       = TomlerProxy(None, fallback=2)
        access_list = ["blah", "bloo"]
        accessed    = proxy[*access_list]
        self.assertEqual(repr(accessed), "<TomlerProxy: <root>.blah.bloo:Any>")

    def test_call_get_value(self):
        proxy = TomlerProxy(5, fallback=2)
        self.assertEqual(proxy(), 5)

    def test_call_get_None_value(self):
        proxy = TomlerProxy(None, fallback=2)
        self.assertEqual(proxy(), None)

    def test_call_get_fallback(self):
        proxy = TomlerProxy((None,), fallback=2)
        self.assertEqual(proxy(), 2)

    def test_call_wrapper(self):
        proxy = TomlerProxy((None,), fallback=2)
        self.assertEqual(proxy(wrapper=lambda x: x*2), 4)

    def test_call_wrapper_error(self):
        def bad_wrapper(val):
            raise TypeError()

        proxy = TomlerProxy(None, fallback=2)
        with self.assertRaises(TypeError):
            proxy(wrapper=bad_wrapper)

    def test_types(self):
        proxy = TomlerProxy(True, fallback=2, types=int)
        self.assertTrue(proxy)

    def test_types_fail(self):
        with self.assertRaises(TypeError):
            TomlerProxy(None, fallback="blah", types=int)

    def test_proxy_inject(self):
        proxy1 = TomlerProxy(None, fallback=2, types=int)
        proxy2 = proxy1._inject(5)
        self.assertEqual(proxy2(), 5)

    def test_proxy_value_retrieval_typecheck_fail(self):
        proxy1 = TomlerProxy(None, fallback=2, types=int)
        with self.assertRaises(TypeError):
            proxy1._inject("blah")()

    def test_proxy_inject_index_update(self):
        proxy1 = TomlerProxy(None, fallback=2, types=int).blah.bloo
        proxy2 = proxy1._inject(5).awef
        self.assertEqual(proxy1._index(), ["<root>", "blah", "bloo"])
        self.assertEqual(proxy2._index(), ["<root>", "blah", "bloo", "awef"])
        self.assertEqual(proxy2(), 5)


##-- ifmain
if __name__ == '__main__':
    unittest.main()
##-- end ifmain
