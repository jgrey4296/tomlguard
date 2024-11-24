#!/usr/bin/env python3
"""
A Proxy for TomlGuard,
  which allows you to use the default attribute access
  (data.a.b.c)
  even when there might not be an `a.b.c` path in the data.

  Thus:
  data.on_fail(default_value).a.b.c()

  Note: To distinguish between not giving a default value,
  and giving a default value of `None`,
  wrap the default value in a tuple: (None,)
"""

# Imports:
##-- builtin imports
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
from types import UnionType
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, NoReturn, Protocol, Sequence, Tuple,
                    TypeAlias, TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 1st party imports
from tomlguard import TomlTypes
from tomlguard._base import GuardBase
from tomlguard.error import TomlAccessError
from tomlguard.proxies.base import NullFallback, TomlGuardProxy

# ##-- end 1st party imports

##-- end builtin imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class TomlGuardFailureProxy(TomlGuardProxy):
    """
    A Wrapper for guarded access to toml values.
    you get the value by calling it.
    Until then, it tracks attribute access,
    and reports that to GuardBase when called.
    It also can type check its value and the value retrieved from the toml data
    """

    def __init__(self, data:GuardBase, types:Any=None, index:list[str]|None=None, fallback:TomlTypes|NullFallback=NullFallback):
        super().__init__(data, types=types, index=index)
        if fallback == (None,):
            self._fallback = None
        else:
            self._fallback = fallback

        if fallback:
            self._match_type(self._fallback)

    def __call__(self, wrapper:callable[[TomlTypes], Any]|None=None, fallback_wrapper:callable[[TomlTypes], Any]|None=None) -> Any:
        """
        Reify a proxy into an actual value, or its fallback.
        Optionally call a wrapper function on the actual value,
        or a fallback_wrapper function on the fallback
        """
        self._notify()
        wrapper : callable[[TomlTypes], TomlTypes] = wrapper or (lambda x: x)
        fallback_wrapper                           = fallback_wrapper or (lambda x: x)
        match self._data, self._fallback:
            case x, y if x is NullFallback and y is NullFallback:
                raise ValueError("No Value, and no fallback")
            case x, None if x is NullFallback or x is None:
                val = None
            case x, data if x is NullFallback or x is None:
                val = fallback_wrapper(data)
            case GuardBase() as data, _:
                val = wrapper(dict(data))
            case _ as data, _:
                val = wrapper(data)

        return self._match_type(val)

    def __getattr__(self, attr:str) -> TomlGuardProxy:
        try:
            match self._data:
                case x if x is NullFallback:
                    raise TomlAccessError()
                case GuardBase():
                    return self._inject(self._data[attr], attr=attr)
                case _:
                    return self._inject(attr=attr)
        except TomlAccessError:
            return self._inject(clear=True, attr=attr)

    def __getitem__(self, keys:str|tuple[str]) -> TomlGuardProxy:
        curr = self
        match keys:
            case tuple():
                for key in keys:
                    curr = curr.__getattr__(key)
            case str():
                curr = self.__getattr__(keys)

        return curr

    def _inject(self, val:tuple[Any]=NullFallback, attr:str|None=None, clear:bool=False) -> TomlGuardProxy:
        match val:
            case _ if clear:
                val = NullFallback
            case x if x is NullFallback:
                val = self._data
            case _:
                pass

        return TomlGuardFailureProxy(val,
                                     types=self._types,
                                     index=self._index(attr),
                                     fallback=self._fallback)
