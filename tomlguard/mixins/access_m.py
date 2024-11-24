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

from collections import ChainMap
from collections.abc import Mapping, ItemsView, KeysView, ValuesView
from tomlguard.error import TomlAccessError

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

super_get             = object.__getattribute__
super_set             = object.__setattr__

class TomlAccess_m:
    """ """

    def __setattr__(self, attr:str, value:TomlTypes) -> None:
        if not getattr(self, "__mutable"):
            raise TypeError()
        super_set(self, attr, value)

    def __getattr__(self, attr:str) -> GuardBase | TomlTypes | list[GuardBase]:
        table = self._table()

        if attr not in table and attr.replace("_", "-") not in table:
            index     = self._index() + [attr]
            index_s   = ".".join(index)
            available = " ".join(self.keys())
            raise TomlAccessError(f"{index_s} not found, available: [{available}]")

        match table.get(attr, None) or table.get(attr.replace("_", "-"), None):
            case dict() as result:
                return self.__class__(result, index=self._index() + [attr])
            case list() as result if all(isinstance(x, dict) for x in result):
                index = self._index()
                return [self.__class__(x, index=index[:]) for x in result if isinstance(x, dict)]
            case _ as result:
                return result

    def __getitem__(self, keys:str|list[str]|tuple[str]) -> TomlTypes:
        curr : typing.Self = self
        match keys:
            case tuple():
                for key in keys:
                    curr = curr.__getattr__(key)
            case str():
                curr = self.__getattr__(keys)
            case _:
                pass

        return curr


    def get(self, key:str, default:TomlTypes|None=None) -> TomlTypes|None:
        if key in self:
            return self[key]

        return default
