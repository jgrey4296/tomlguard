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

from tomler.error import TomlAccessError
from tomler.base import TomlerBase
from tomler.tomler import Tomler
from tomler.utils.proxy import TomlerProxy
from tomler.utils.iter_proxy import TomlerIterProxy

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
        self.assertIsInstance(proxied, TomlerProxy)
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

    def test_proxy_false_value_retrieval(self):
        base    = Tomler({"test": None})
        proxied = base.on_fail("aweg").test
        self.assertEqual(base.test, None)
        self.assertIsInstance(proxied, TomlerProxy)
        self.assertEqual(proxied(), None)

    def test_proxy_nested_false_value_retrieval(self):
        base     = Tomler({"top": {"mid": {"bot": None}}})
        proxied = base.on_fail("aweg").top.mid.bot
        self.assertIsInstance(proxied, TomlerProxy)
        self.assertEqual(proxied(), None)

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
        self.assertIsInstance(proxied, TomlerProxy)

    def test_proxy_multi_use(self):
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        proxied = base.on_fail("aweg").test.blah
        self.assertEqual(proxied.bloo(), "final")
        self.assertEqual(proxied.aweg(), "joijo")

    @mock.patch.object(TomlerBase, "_defaulted", set())
    def test_proxied_report_empty(self):
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        self.assertEqual(Tomler.report_defaulted(), [])

    @mock.patch.object(TomlerBase, "_defaulted", set())
    def test_proxied_report_no_existing_values(self):
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.test.blah.bloo
        base.test.blah.aweg
        self.assertEqual(Tomler.report_defaulted(), [])

    @mock.patch.object(TomlerBase, "_defaulted", set())
    def test_proxied_report_missing_values(self):
        base              = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.on_fail(False).this.doesnt.exist()
        base.on_fail(False).test.blah.other()

        defaulted = Tomler.report_defaulted()
        self.assertIn("<root>.this.doesnt.exist = false # <Any>", defaulted)
        self.assertIn("<root>.test.blah.other = false # <Any>", defaulted)

    @mock.patch.object(TomlerBase, "_defaulted", set())
    def test_proxied_report_missing_typed_values(self):
        base     = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.on_fail("aValue", str).this.doesnt.exist()
        base.on_fail(2, int).test.blah.other()

        defaulted = Tomler.report_defaulted()
        self.assertIn("<root>.this.doesnt.exist = 'aValue' # <str>", defaulted)
        self.assertIn("<root>.test.blah.other = 2 # <int>", defaulted)

    @unittest.skip("not implemented")
    def test_proxied_report_no_duplicates(self):
        raise NotImplementedError()

    def test_proxied_flatten(self):
        base  = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        proxy = base.flatten_on({})
        self.assertIsInstance(proxy, TomlerIterProxy)

    def test_proxied_flatten_call(self):
        base   = Tomler({"test": { "blah": [{"bloo": "final", "aweg": "joijo"}, {"other": 5}]}})
        result = base.flatten_on({}).test.blah()
        self.assertEqual(dict(result), {"bloo": "final", "aweg": "joijo", "other": 5})

    def test_proxied_flatten_fallback(self):
        base   = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        result = base.flatten_on({}).test.blah()
        self.assertIsInstance(result, dict)

    def test_proxied_flatten_fallback_valued(self):
        base   = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        result = base.flatten_on({"a": "test"}).test.blah()
        self.assertEqual(result, {"a": "test"})

    def test_proxied_bad_fallback(self):
        base   = Tomler({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        with self.assertRaises(TypeError):
            base.flatten_on(2)

##-- ifmain
if __name__ == '__main__':
    unittest.main()
##-- end ifmain
