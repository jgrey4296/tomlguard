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

from tomler.tomler import TomlerBase, TomlAccessError, Tomler

class TestBaseTomler(unittest.TestCase):
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
        basic = TomlerBase({"test": "blah"})
        self.assertTrue(basic)

    def test_basic_access(self):
        basic = TomlerBase({"test": "blah"})
        self.assertEqual(basic.test, "blah")

    def test_basic_item_access(self):
        basic = TomlerBase({"test": "blah"})
        self.assertEqual(basic['test'], "blah")

    def test_multi_item_access(self):
        basic = TomlerBase({"test": {"blah": "bloo"}})
        self.assertEqual(basic['test', "blah"], "bloo")

    def test_basic_access_error(self):
        basic = TomlerBase({"test": "blah"})
        with self.assertRaises(TomlAccessError):
            basic.none_existing

    def test_item_access_error(self):
        basic = TomlerBase({"test": "blah"})
        with self.assertRaises(TomlAccessError):
            basic['non_existing']

    def test_nested_access(self):
        basic = TomlerBase({"test": {"blah": 2}})
        self.assertEqual(basic.test.blah, 2)

    def test_repr(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        self.assertEqual(repr(basic), "<Tomler:['test', 'bloo']>")

    def test_immutable(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        with self.assertRaises(TypeError):
            basic.test = 5

    def test_uncallable(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        with self.assertRaises(TomlAccessError):
            basic()

    def test_iter(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        pairs = list(basic)
        self.assertEqual(pairs, [("test", {"blah":2}), ("bloo", 2)])

    def test_contains(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        self.assertTrue("test" in basic)

    def test_contains_fail(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        self.assertFalse("blah" in basic)

    def test_get(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        self.assertEqual(basic.get("bloo"), 2)

    def test_get_default(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        self.assertIsNone(basic.get("blah"))

    def test_get_default_value(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        self.assertEqual(basic.get("blah", 5), 5)

    def test_keys(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        self.assertEqual(basic.keys(), ["test", "bloo"])

    def test_items(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        self.assertEqual(list(basic.items()), [("test", {"blah": 2}), ("bloo", 2)])

    def test_values(self):
        basic = TomlerBase({"test": {"blah": 2}, "bloo": 2})
        self.assertEqual(list(basic.values()), [{"blah": 2}, 2])

    def test_list_access(self):
        basic = TomlerBase({"test": {"blah": [1,2,3]}, "bloo": ["a","b","c"]})
        self.assertEqual(basic.test.blah, [1,2,3])
        self.assertEqual(basic.bloo, ["a","b","c"])


class TestProxiedTomler(unittest.TestCase):
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
        pass

class TestLoaderTomler(unittest.TestCase):
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
        pass

class TestTomlerMerge(unittest.TestCase):
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
        simple = Tomler.merge({"a":2}, {"b": 5})
        self.assertIsInstance(simple, Tomler)
        self.assertEqual(simple._table(), {"a": 2, "b": 5})

    def test_merge_conflict(self):
        with self.assertRaises(KeyError):
            Tomler.merge({"a":2}, {"a": 5})

    def test_merge_with_shadowing(self):
        basic = Tomler.merge({"a":2}, {"a": 5, "b": 5}, shadow=True)
        self.assertEqual(dict(basic), {"a":2, "b": 5})


##-- ifmain
if __name__ == '__main__':
    unittest.main()
##-- end ifmain
