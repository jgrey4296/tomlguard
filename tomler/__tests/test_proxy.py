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

from tomler.tomler import TomlerProxy

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
        proxy = TomlerProxy(2)
        self.assertTrue(proxy)

    def test_attr(self):
        proxy = TomlerProxy(2)
        proxy.blah.bloo
        self.assertEqual(repr(proxy), "<TomlerProxy: <root>.blah.bloo:Any>")

    def test_item(self):
        proxy = TomlerProxy(2)
        proxy['blah']['bloo']
        self.assertEqual(repr(proxy), "<TomlerProxy: <root>.blah.bloo:Any>")


    def test_multi_item(self):
        proxy = TomlerProxy(2)
        proxy['blah', 'bloo']
        self.assertEqual(repr(proxy), "<TomlerProxy: <root>.blah.bloo:Any>")

    def test_multi_item_expansion(self):
        proxy = TomlerProxy(2)
        access_list = ["blah", "bloo"]
        proxy[*access_list]
        self.assertEqual(repr(proxy), "<TomlerProxy: <root>.blah.bloo:Any>")

    def test_call_basic(self):
        proxy = TomlerProxy(2)
        self.assertEqual(proxy(), 2)

    def test_call_wrapper(self):
        proxy = TomlerProxy(2)
        self.assertEqual(proxy(wrapper=lambda x: x*2), 4)

    def test_call_wrapper_error(self):
        def bad_wrapper(val):
            raise TypeError()

        proxy = TomlerProxy(2)
        with self.assertRaises(TypeError):
            proxy(wrapper=bad_wrapper)

    def test_types(self):
        proxy = TomlerProxy(2, int)
        self.assertTrue(proxy)

    def test_types_fail(self):
        with self.assertRaises(TypeError):
            TomlerProxy("blah", int)

    def test_proxy_inject(self):
        proxy1 = TomlerProxy(2, int)
        proxy2 = proxy1.inject(5)
        self.assertEqual(proxy2(), 5)

    def test_proxy_inject_typecheck_fail(self):
        proxy1 = TomlerProxy(2, int)
        with self.assertRaises(TypeError):
            proxy1.inject("blah")

    def test_proxy_inject_index_update(self):
        proxy1 = TomlerProxy(2, int).blah.bloo
        proxy2 = proxy1.inject(5).awef
        self.assertEqual(proxy1._index(), ["<root>", "blah", "bloo"])
        self.assertEqual(proxy2._index(), ["<root>", "blah", "bloo", "awef"])
        self.assertEqual(proxy2(), 5)


##-- ifmain
if __name__ == '__main__':
    unittest.main()
##-- end ifmain
