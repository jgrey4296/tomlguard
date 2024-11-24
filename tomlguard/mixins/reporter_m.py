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
import time
import types
import weakref
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

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class DefaultedReporter_m:

    _defaulted : ClassVar[set[str]] = set()

    @staticmethod
    def add_defaulted(index:str|list[str], val:TomlTypes, types:str="Any") -> None:
        match index, val:
            case list(), _:
                raise TypeError("Tried to Register a default value with a list index, use a str")
            case str(), bool():
                index_str = f"{index} = {str(val).lower()} # <{types}>"
            case str(), _:
                index_str = f"{index} = {repr(val)} # <{types}>"
            case [*xs], bool():
                index_path = ".".join(xs)
                index_str = f"{index_path} = {str(val).lower()} # <{types}>"
            case [*xs], _:
                index_path = ".".join(xs)
                index_str = f"{index_path} = {val} # <{types}>"
            case _, _:
                raise TypeError("Unexpected Values found: ", val, index)

        DefaultedReporter_m._defaulted.add(index_str)

    @staticmethod
    def report_defaulted() -> list[str]:
        """
        Report the index paths inject default values
        """
        return list(DefaultedReporter_m._defaulted)
