#!/usr/bin/env python3
"""

"""
# Imports:
from __future__ import annotations

# ##-- stdlib imports
import abc
import atexit#  for @atexit.register
import collections
import contextlib
import datetime
import enum
import faulthandler
import functools as ftz
import hashlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import types
import warnings
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from time import sleep
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest

# ##-- end 3rd party imports

# ##-- 1st party imports
from tomlguard._base import GuardBase
from tomlguard.error import TomlAccessError
from tomlguard.proxies.failure import TomlGuardFailureProxy
from tomlguard.tomlguard import TomlGuard
from tomlguard.mixins.reporter_m import DefaultedReporter_m

# ##-- end 1st party imports

logging = logmod.root

class TestDefaultedReporter:

    @pytest.fixture(scope="function")
    def setup(self):
        pass

    @pytest.fixture(scope="function")
    def cleanup(self):
        pass

    def test_sanity(self):
        assert(True is True)

    def test_proxied_report_empty(self, mocker):
        mocker.patch.object(DefaultedReporter_m, "_defaulted", set())
        base     = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        assert(TomlGuard.report_defaulted() == [])

    def test_proxied_report_no_existing_values(self, mocker):
        mocker.patch.object(DefaultedReporter_m, "_defaulted", set())
        base     = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.test.blah.bloo
        base.test.blah.aweg
        assert(TomlGuard.report_defaulted() == [])

    def test_proxied_report_missing_values(self, mocker):
        mocker.patch.object(DefaultedReporter_m, "_defaulted", set())
        base              = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.on_fail(False).this.doesnt.exist()
        base.on_fail(False).test.blah.other()

        defaulted = TomlGuard.report_defaulted()
        assert("<root>.this.doesnt.exist = false # <Any>" in defaulted)
        assert("<root>.test.blah.other = false # <Any>" in defaulted)

    def test_proxied_report_missing_typed_values(self, mocker):
        mocker.patch.object(DefaultedReporter_m, "_defaulted", set())
        base     = TomlGuard({"test": { "blah": {"bloo": "final", "aweg": "joijo"}}})
        base.on_fail("aValue", str).this.doesnt.exist()
        base.on_fail(2, int).test.blah.other()

        defaulted = TomlGuard.report_defaulted()
        assert("<root>.this.doesnt.exist = 'aValue' # <str>" in defaulted)
        assert("<root>.test.blah.other = 2 # <int>" in defaulted)

    @pytest.mark.skip("not implemented")
    def test_proxied_report_no_duplicates(self):
        raise NotImplementedError()
