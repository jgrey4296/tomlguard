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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1

##-- end builtin imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from collections import ChainMap
from tomlguard.base import TomlTypes, GuardBase
from tomlguard.error import TomlAccessError
from tomlguard.utils.proxy import TomlGuardProxy, NullFallback

class TomlGuardIterProxy(TomlGuardProxy):
    pass

class TomlGuardIterFirstProxy(TomlGuardIterProxy):
    """
    A Proxy which handles lists by getting the first applicable value
    when passing through lists.
    So instead of:
    data.val.subval.listval[0].name
    it can be:
    data.first_of().val.subval.listval.name()

    """

    def __init__(self, data, types=None, index=None, subindex=None, fallback=NullFallback, nested=False):
        super().__init__(data, types=types, index=index, fallback=fallback)
        self._nested    = False
        self.__subindex = subindex or []

    def __repr__(self) -> str:
        type_str     = self._types_str()
        index_str    = ".".join(self._index())
        subindex_str = ".".join(self._subindex())
        return f"<TomlGuardIterFirstProxy: {index_str}:{subindex_str} ({self._fallback}) <{type_str}> >"

    def __call__(self, wrapper=None, fallback_wrapper=None) -> TomlTypes:
        if not self._nested and self._data is not NullFallback and all(isinstance(x, TomlGuardIterFirstProxy) for x in self._data):
            return self._get_first(wrapper=wrapper, fallback_wrapper=fallback_wrapper)

        return super().__call__(wrapper=wrapper, fallback_wrapper=fallback_wrapper)

    def _get_first(self, wrapper, fallback_wrapper) -> TomlTypes:
        """
        get the first value from any available table in an array
        """
        assert(isinstance(self._data, list))
        for val in self._data:
            assert(isinstance(val, TomlGuardIterFirstProxy))
            result = val(wrapper=wrapper, fallback_wrapper=fallback_wrapper)
            if result is None:
                continue
            return result

    def __iter__(self) -> Iterator[TomlTypes]:
        return iter(self())

    def _subindex(self, sub:str|None=None) -> list[str]:
        if sub is None:
            return self.__subindex[:]
        return self.__subindex[:] + [sub]

    def __getattr__(self, attr:str) -> TomlGuardProxy:
        try:
            match self._data:
                case list() if all(isinstance(x, (GuardBase, TomlGuardProxy)) for x in self._data):
                    return self._nested_inject(attr)
                case GuardBase():
                    return self._inject(self._data, attr=attr)
                case None:
                    raise TomlAccessError()
                case _:
                    return self._inject(attr=attr)
        except TomlAccessError:
            result = self._inject(clear=True, attr=attr)
            return result

    def _inject(self, val:tuple[Any]=NullFallback, attr:str|None=None, clear:bool=False) -> TomlGuardProxy:
        match val:
            case _ if clear:
                val = NullFallback
            case x if x is NullFallback:
                val = self._data
            case _:
                val = val[attr]

        return TomlGuardIterFirstProxy(val,
                                       types=self._types,
                                       index=self._index(attr),
                                       fallback=self._fallback)


    def _nested_inject(self, attr=None, clear=None) -> TomlGuardIterProxy|None:
        sub_proxies = []
        assert(isinstance(self._data, list))
        index    = self._index()
        subindex = self._subindex(attr)
        for data in self._data:
            match data:
                case x if x is NullFallback:
                    continue
                case TomlGuardIterFirstProxy() | GuardBase() if attr not in data:
                    continue
                case GuardBase():
                    new_proxy = TomlGuardIterFirstProxy(data[attr],
                                                        types=self._types,
                                                        fallback=self._fallback,
                                                        index=index,
                                                        subindex=subindex,
                                                        nested=True)
                case TomlGuardIterFirstProxy():
                    new_proxy = data[attr]

            sub_proxies.append(new_proxy)

        if not bool(sub_proxies):
            raise TomlAccessError()

        return TomlGuardIterFirstProxy(sub_proxies,
                                       types=self._types,
                                       fallback=self._fallback,
                                       index=index,
                                       subindex=subindex)


    def _match_type(self, val:TomlTypes) -> TomlTypes:
        return val

class TomlGuardIterAllProxy(TomlGuardIterProxy):
    """
    A Proxy for lists and dicts, which can flatten, or match particulars
    """

    def __init__(self, data, types=None, index=None, subindex=None, fallback=NullFallback, kind="first"):
        super().__init__(data, types=types, index=index, fallback=fallback)
        if self._fallback and not isinstance(self._fallback, Iterable):
            raise TypeError("Iter Proxy needs an iterable")
        self.__subindex = subindex or []

    def __repr__(self) -> str:
        type_str     = self._types_str()
        index_str    = ".".join(self._index())
        subindex_str = ".".join(self._subindex())
        return f"<TomlGuardIterAllProxy: {index_str}:{subindex_str} ({self._fallback}) <{type_str}> >"

    def __call__(self, wrapper=None) -> TomlTypes:
        self._notify()
        wrapper = wrapper or (lambda x: x)
        wrapped = wrapper(val)
        return self._match_type(wrapped)

    def __iter__(self) -> Iterator[TomlTypes]:
        return iter(self())

    def _subindex(self) -> list[str]:
        return self.__subindex[:]

    def _get_all(self) -> list[TomlTypes]:
        """
        Get all matching values from array of tables
        """
        match self._data, self._fallback:
            case [] | NullFallback(), NullFallback():
                pass
            case [] | NullFallback(), val:
                return val
            case [*vals], _:
                result = []
                for val in vals:
                    result += val
                return result

        base_index = ".".join(self._index())
        sub_index = ".".join(self._subindex())
        raise TomlAccessError(f"TomlGuardIterProxy Failure: {base_index}[?].{sub_index}")

    def _inject(self, val=NullFallback, attr=None, clear=None) -> TomlGuardIterProxy:
        match val:
            case NullFallback():
                val = self._data
            case _ if clear:
                val = NullFallback
            case _:
                val = val or self._data
        if clear:
            val = None

        return TomlGuardIterAllProxy(val,
                                     types=self._types,
                                     fallback=self._fallback,
                                     index=self._index(attr),
                                     subindex=new_index)

    def _match_type(self, val:TomlTypes) -> TomlTypes:
        return val

class TomlGuardIterFlatProxy(TomlGuardIterProxy):
    """
    A Proxy for lists and dicts, which can flatten, or match particulars
    """

    def __init__(self, data, types=None, index=None, subindex=None, fallback=None, kind="first"):
        super().__init__(data, types=types, index=index, fallback=fallback)
        if self._fallback and not isinstance(self._fallback, Iterable):
            raise TypeError("Iter Proxy needs an iterable")
        self.__subindex = subindex or []

    def __repr__(self) -> str:
        type_str     = self._types_str()
        index_str    = ".".join(self._index())
        subindex_str = ".".join(self._subindex())
        return f"<TomlGuardIterFlatProxy: {index_str}:{subindex_str} ({self._fallback}) <{type_str}> >"

    def __call__(self, wrapper=None) -> TomlTypes:
        self._notify()
        wrapper = wrapper or (lambda x: x)
        wrapped = wrapper(val)
        return self._match_type(wrapped)

    def __iter__(self) -> Iterator[TomlTypes]:
        return iter(self())

    def __getattr__(self, attr:str) -> TomlGuardIterProxy:
        try:
            match self._data:
                case GuardBase():
                    return self._inject(self._data[attr], attr=attr)
                case None:
                    raise TomlAccessError()
                case _:
                    return self._inject(attr=attr)
        except TomlAccessError:
            return self._inject(clear=True, attr=attr)

    def _subindex(self) -> list[str]:
        return self.__subindex[:]

    def _get_flat(self) -> GuardBase | list[TomlTypes]:
        match self._data:
            case [] | (None,):
                pass
            case [*vals]:
                return ChainMap(*(dict(x) for x in vals))

        match self._fallback:
            case (None,):
                pass
            case None:
                return None
            case dict() as x:
                return x

        base_index = ".".join(self._index())
        sub_index = ".".join(self._subindex())
        raise TomlAccessError(f"TomlGuardIterProxy Failure: {base_index}[?].{sub_index}")

    def _inject(self, val=None, attr=None, clear=None) -> TomlGuardIterProxy:
        new_index = self._subindex()
        if attr:
            new_index.append(attr)

        val = val or self._data
        if clear:
            val = None

        return TomlGuardIterFlatProxy(val, types=self._types, fallback=self._fallback, index=self._index(), subindex=new_index)

    def _match_type(self, val:TomlTypes) -> TomlTypes:
        return val

class TomlGuardIterMatchProxy(TomlGuardIterProxy):
    """
    A Proxy for lists and dicts, which can flatten, or match particulars
    """

    def __init__(self, data, types=None, index=None, subindex=None, fallback=None, kind="first"):
        super().__init__(data, types=types, index=index, fallback=fallback)
        if self._fallback and not isinstance(self._fallback, Iterable):
            raise TypeError("Iter Proxy needs an iterable")
        self.__subindex = subindex or []

    def __repr__(self) -> str:
        type_str     = self._types_str()
        index_str    = ".".join(self._index())
        subindex_str = ".".join(self._subindex())
        return f"<TomlGuardIterMatchProxy: {index_str}:{subindex_str} ({self._fallback}) <{type_str}> >"

    def __call__(self, wrapper=None) -> TomlTypes:
        self._notify()
        wrapper = wrapper or (lambda x: x)
        wrapped = wrapper(val)
        return self._match_type(wrapped)

    def __iter__(self) -> Iterator[TomlTypes]:
        return iter(self())

    def _subindex(self) -> list[str]:
        return self.__subindex[:]

    def _get_match(self) -> GuardBase | TomlTypes:
        """
        Get a table from an array if it matches a set of key=value pairs
        """
        for entry in self._data:
            try:
                for x in self._subindex():
                    entry = getattr(entry, x)
                if all(getattr(entry, x) == y for x,y in elf._kind.items()):
                    return entry
            except TomlAccessError:
                continue

        base_index = ".".join(self._index())
        sub_index = ".".join(self._subindex())
        raise TomlAccessError(f"TomlGuardIterProxy Match Failure: {base_index}[?].{sub_index} != {self._match}")

    def _inject(self, val=None, attr=None, clear=None) -> TomlGuardIterProxy:
        new_index = self._subindex()
        if attr:
            new_index.append(attr)

        val = val or self._data
        if clear:
            val = None

        return TomlGuardIterProxy(val, types=self._types, fallback=self._fallback, index=self._index(), subindex=new_index)

    def _match_type(self, val:TomlTypes) -> TomlTypes:
        return val
