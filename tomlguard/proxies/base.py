#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import abc
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
                    Generic, Iterable, Iterator, Mapping, Match, NoReturn,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

from tomlguard._base import GuardBase
from tomlguard.mixins.reporter_m import DefaultedReporter_m

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

NullFallback = NoReturn

class TomlGuardProxy:
    """ A Base Class for Proxies """

    def __init__(self, data:GuardBase, types:Any=None, index:list[str]|None=None, fallback:TomlTypes|NullFallback=NullFallback):
        super().__init__()
        self._types                         = types or Any
        self._data                          = data
        self.__index : list[str]            = index or ["<root>"]

    def __repr__(self) -> str:
        type_str = self._types_str()
        index_str = ".".join(self._index())
        return f"<TomlGuardProxy: {index_str}:{type_str}>"

    def __len__(self) -> int:
        if hasattr(self._data, "__len__"):
            return len(self._data)

        return 0

    def __bool__(self) -> bool:
        return self._data is not None and self._data is not NullFallback

    def __call__(self, *, wrapper:callable[[TomlTypes], Any]|None=None, **kwargs) -> Any:
        return None


    def _inject(self, val:tuple[Any]=NullFallback, attr:str|None=None, clear:bool=False) -> TomlGuardProxy:
        match val:
            case _ if clear:
                val = NullFallback
            case x if x is NullFallback:
                val = self._data
            case _:
                pass

        return TomlGuardProxy(val,
                              types=self._types,
                              index=self._index(attr),
                              fallback=self._fallback)

    def _notify(self) -> None:
        types_str = self._types_str()
        match self._data, self._fallback, self._index():
            case GuardBase(), _, _:
                pass
            case _, _, []:
                pass
            case x , val, [*index] if x is NullFallback:
                DefaultedReporter_m.add_defaulted(".".join(index), val, types_str)
            case val, _, [*index]:
                DefaultedReporter_m.add_defaulted(".".join(index), val, types_str)
            case val, flbck, index,:
                raise TypeError("Unexpected Values found: ", val, index, flbck)

    def _types_str(self) -> str:
        match self._types:
            case types.UnionType() as targ:
                types_str = repr(targ)
            case type(__name__=targ):
                types_str = targ
            case _ as targ:
                types_str = str(targ)

        return types_str

    def _match_type(self, val:TomlTypes) -> TomlTypes:
        if self._types != Any and not isinstance(val, self._types):
            types_str = self._types_str()
            index_str  = ".".join(self.__index + ['(' + types_str + ')'])
            raise TypeError("TomlProxy Value doesn't match declared Type: ", index_str, val, self._types)

        return val

    def _index(self, sub:str=None) -> list[str]:
        if sub is None:
            return self.__index[:]
        return self.__index[:] + [sub]
