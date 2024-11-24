
#!/usr/bin/env python3
"""

"""

##-- builtin imports
from __future__ import annotations

# import abc
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
import typing
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1

try:
    # for py 3.10 onwards:
    from typing import TypeAlias
except ImportError:
    TypeAlias = Any

##-- end builtin imports

from collections import ChainMap
from collections.abc import Mapping, ItemsView, KeysView, ValuesView
from tomlguard.error import TomlAccessError
from tomlguard import TomlTypes
from tomlguard.mixins.access_m import super_get, super_set

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

dict_items = type({}.items())


class GuardBase(Mapping[str, TomlTypes]):
    """
    Provides access to toml data (TomlGuard.load(apath))
    but as attributes (data.a.path.in.the.data)
    instead of key access (data['a']['path']['in']['the']['data'])

    while also providing typed, guarded access:
    data.on_fail("test", str | int).a.path.that.may.exist()

    while it can then report missing paths:
    data.report_defaulted() -> ['a.path.that.may.exist.<str|int>']
    """

    def __init__(self, data:dict[str,TomlTypes]=None, *, index:None|list[str]=None, mutable:bool=False):
        super().__init__()
        super_set(self, "__table", data or {})
        super_set(self, "__index"   , (index or ["<root>"])[:])
        super_set(self, "__mutable" , mutable)

    def __repr__(self) -> str:
        return f"<TomlGuard:{list(self.keys())}>"

    def __len__(self) -> int:
        return len(self._table())

    def __call__(self) -> TomlTypes:
        raise TomlAccessError("Don't call a TomlGuard, call a TomlGuardProxy using methods like .on_fail")

    def __iter__(self):
        return iter(getattr(self, "__table").items())

    def __contains__(self, _key: object) -> bool:
        return _key in self.keys()

    def _index(self) -> list[str]:
        return super_get(self, "__index")[:]

    def _table(self) -> dict[str,TomlTypes]:
        return super_get(self, "__table")

    def keys(self) -> KeysView[str]:
        table = super_get(self, "__table")
        return table.keys()

    def items(self) -> ItemsView[str, TomlTypes]:
        match super_get(self, "__table"):
            case dict() as val:
                return val.items()
            case list() as val:
                return dict({self._index()[-1]: val}).items()
            case GuardBase() as val:
                return val.items()
            case x:
                raise TypeError("Unknown table type", x)

    def values(self) -> ValuesView[TomlTypes]:
        match super_get(self, "__table"):
            case dict() as val:
                return val.values()
            case list() as val:
                return val
            case _:
                raise TypeError()
