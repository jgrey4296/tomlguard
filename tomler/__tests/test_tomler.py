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

from tomler.tomler import TomlerBase, TomlAccessError, Tomler, TomlerProxy

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

    def test_dot_access(self):
        basic = TomlerBase({"test": "blah"})
        self.assertEqual(basic.test, "blah")

    def test_index(self):
        basic = TomlerBase({"test": "blah"})
        self.assertEqual(basic._index(), ["<root>"])

    def test_index_independence(self):
        basic = TomlerBase({"test": "blah"})
        self.assertEqual(basic._index(), ["<root>"])
        basic.test
        self.assertEqual(basic._index(), ["<root>"])

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
        base = Tomler({"test": "blah"})
        proxied = base.on_fail("aweg")
        self.assertIsInstance(proxied, TomlerBase)
        self.assertIsInstance(proxied.doesnt_exist, TomlerProxy)

    def test_proxy_on_existing_key(self):
        base = Tomler({"test": "blah"})
        proxied = base.on_fail("aweg")
        self.assertEqual("blah", proxied.test())

    def test_proxy_on_bad_key(self):
        base    = Tomler({"test": "blah"})
        proxied = base.on_fail("aweg")
        self.assertEqual("aweg", proxied.awehjo())

    def test_proxy_index_independence(self):
        base    = Tomler({"test": "blah"})
        base_val = base.test
        proxied = base.on_fail("aweg")
        good_key = proxied.test
        bad_key = proxied.ajojo

        self.assertEqual(base._index(), ["<root>"])
        self.assertEqual(proxied._index(), ["<root>"])
        self.assertEqual(good_key._index(), ["<root>", "test"])
        self.assertEqual(bad_key._index(), ["<root>", "ajojo"])

    def test_proxy_multi_independence(self):
        base     = Tomler({"test": "blah"})
        proxied  = base.on_fail("aweg")
        proxied2 = base.on_fail("jioji")
        self.assertNotEqual(id(proxied), id(proxied2))
        self.assertEqual("aweg", proxied.awehjo())
        self.assertEqual("jioji", proxied2.awjioq())

    def test_proxy_value_retrieval(self):
        base     = Tomler({"test": "blah"})
        proxied = base.on_fail("aweg").test
        self.assertIsInstance(proxied, TomlerProxy)
        self.assertEqual(proxied(), "blah")

    def test_proxy_nested_value_retrieval(self):
        base     = Tomler({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test.blah.bloo
        self.assertIsInstance(proxied, TomlerProxy)
        self.assertEqual(proxied(), "final")

    def test_proxy_fallback(self):
        base     = Tomler({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test.blah.missing
        self.assertIsInstance(proxied, TomlerProxy)
        self.assertEqual(proxied(), "aweg")

    def test_no_proxy_error(self):
        base     = Tomler({"test": { "blah": {"bloo": "final"}}})
        with self.assertRaises(TomlAccessError):
            base.test.blah()

    def test_proxy_early_check(self):
        base     = Tomler({"test": { "blah": {"bloo": "final"}}})
        proxied = base.on_fail("aweg").test
        self.assertIsInstance(proxied, Tomler)

    def test_proxy_multi_use(self):
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        proxied = base.on_fail("aweg").test.blah
        self.assertEqual(proxied.bloo(), "final")
        self.assertEqual(proxied.aweg(), "joijo")

    def test_proxied_report_empty(self):
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        self.assertEqual(Tomler.report_defaulted(), [])

    def test_proxied_report_no_existing_values(self):
        Tomler._defaulted = []
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.test.blah.bloo
        base.test.blah.aweg
        self.assertEqual(Tomler.report_defaulted(), [])

    def test_proxied_report_missing_values(self):
        Tomler._defaulted = []
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.on_fail(False).this.doesnt.exist()
        base.on_fail(False).test.blah.other()
        self.assertEqual(Tomler.report_defaulted(),
                        ["<root>.this.doesnt.exist = false # <Any>",
                         "<root>.test.blah.other = false # <Any>"])


    def test_proxied_report_missing_typed_values(self):
        Tomler._defaulted = []
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.on_fail("aValue", str).this.doesnt.exist()
        base.on_fail(2, int).test.blah.other()
        self.assertEqual(Tomler.report_defaulted(),
                        ["<root>.this.doesnt.exist = \"aValue\" # <str>",
                         "<root>.test.blah.other = 2 # <int>"])



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
