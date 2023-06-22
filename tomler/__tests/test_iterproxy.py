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

from tomler.tomler import TomlAccessError, TomlerIterProxy

class TestIterProxy(unittest.TestCase):
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
        basic = TomlerIterProxy([5])
        self.assertTrue(basic)

    def test_fail_on_noniterable_value(self):
        with self.assertRaises(TypeError):
            TomlerIterProxy(5)

    def test_fail_on_bad_kind(self):
        with self.assertRaises(TypeError):
            TomlerIterProxy([5], kind="bad")

    def test_default_list_value(self):
        basic = TomlerIterProxy()
        self.assertEqual(basic._value[0], [])

    def test_repr(self):
        basic = TomlerIterProxy([5]).blah.bloo
        self.assertEqual(repr(basic), "<TomlerIterProxy.first: <root>:blah.bloo (None) <Any> >")

    def test_repr_preindex(self):
        basic = TomlerIterProxy([5], index=["blah", "bloo"]).sub.test
        self.assertEqual(repr(basic), "<TomlerIterProxy.first: blah.bloo:sub.test (None) <Any> >")

    def test_attr(self):
        basic = TomlerIterProxy([5], index=["blah", "bloo"]).sub.test
        self.assertEqual(basic._subindex(), ["sub", "test"])
        self.assertEqual(basic._index(), ["blah", "bloo"])

    def test_item_updates_subindex(self):
        basic = TomlerIterProxy([5], index=["blah", "bloo"])['sub']['test']
        self.assertEqual(basic._subindex(), ["sub", "test"])
        self.assertEqual(basic._index(), ["blah", "bloo"])

    def test_multi_item(self):
        basic = TomlerIterProxy([5], index=["blah", "bloo"])['sub', 'test']
        self.assertEqual(basic._subindex(), ["sub", "test"])
        self.assertEqual(basic._index(), ["blah", "bloo"])

    def test_call_first(self):
        basic = TomlerIterProxy([[5], [10]])
        self.assertEqual(basic(), 5)

    def test_call_first_non_empty(self):
        basic = TomlerIterProxy([[], [10]])
        self.assertEqual(basic(), 10)

    def test_call_first_fallback(self):
        basic = TomlerIterProxy([[], []], fallback=2)
        self.assertEqual(basic(), 2)

    def test_call_first_no_fallback(self):
        basic = TomlerIterProxy([[], []])
        with self.assertRaises(TomlAccessError):
            basic()

    def test_call_all_simple(self):
        basic = TomlerIterProxy([5, 10, 15], kind="all")
        self.assertEqual(basic(), [5, 10, 15])

    def test_call_all_lists(self):
        basic = TomlerIterProxy([[5, 10, 15], ["a","b","c"]], kind="all")
        self.assertEqual(basic(), [[5, 10, 15], ["a","b","c"]])

    def test_call_all_empty_list(self):
        basic = TomlerIterProxy([], kind="all")
        with self.assertRaises(TomlAccessError):
            basic()

    def test_call_all_allow_empty_list(self):
        basic = TomlerIterProxy([], kind="all", fallback=[])
        self.assertEqual(basic(), [])

    def test_call_all_allow_None(self):
        basic = TomlerIterProxy([], kind="all", fallback=(None,))
        self.assertEqual(basic(), None)

    def test_basic_flat_dict_allow_None(self):
        basic = TomlerIterProxy([], kind="flat", fallback=(None,))
        self.assertEqual(basic(), None)

    def test_basic_flat_dict_simple(self):
        basic = TomlerIterProxy([{"a":2}, {"b": 5}], kind="flat", fallback=(None,))
        self.assertEqual(basic()._table(), {"a":2, "b": 5})

    def test_basic_flat_dict_conflict(self):
        basic = TomlerIterProxy([{"a":2}, {"a": 5}], kind="flat", fallback=(None,))
        with self.assertRaises(KeyError):
            basic()

    def test_basic_flat_list(self):
        basic = TomlerIterProxy([[1,2,3], [4,5,6]], kind="flat")
        self.assertEqual(basic(), [1,2,3,4,5,6])


##-- ifmain
if __name__ == '__main__':
    unittest.main()
##-- end ifmain
