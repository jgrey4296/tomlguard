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
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1

##-- end builtin imports

##-- boltons
# import boltons.cacheutils
# import boltons.debugutils
# import boltons.deprutils
# import boltons.dictutils
# import boltons.easterutils
# import boltons.ecoutils
# import boltons.excutils
# import boltons.fileutils
# import boltons.formatutils
# import boltons.funcutils
# import boltons.gcutils
# import boltons.ioutils
# import boltons.iterutils
# import boltons.jsonutils
# import boltons.listutils
# import boltons.mathutils
# import boltons.mboxutils
# import boltons.namedutils
# import boltons.pathutils
# import boltons.queueutils
# import boltons.setutils
# import boltons.socketutils
# import boltons.statsutils
# import boltons.strutils
# import boltons.tableutils
# import boltons.tbutils
# import boltons.timeutils
# import boltons.typeutils
# import boltons.urlutils
##-- end boltons

##-- lib imports
# from bs4 import BeautifulSoup
# import construct as C
# import dirty-equals as deq
# import graphviz
# import matplotlib.pyplot as plt
import more_itertools as mitz
# import networkx as nx
# import numpy as np
# import pandas
# import pomegranate as pom
# import pony import orm
# import pronouncing
# import pyparsing as pp
# import rich
# import seaborn as sns
# import sklearn
# import spacy # nlp = spacy.load("en_core_web_sm")
# import stackprinter # stackprinter.set_excepthook(style='darkbg2')
# import sty
# import sympy
# import tomllib
# import toolz
# import tqdm
# import validators
# import z3
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from collections import ChainMap
from tomler.base import TomlTypes, TomlerBase
from tomler.error import TomlAccessError
from tomler.utils.proxy import TomlerProxy

class TomlerIterProxy(TomlerProxy):
    """
    A Proxy for lists and dicts, which can flatten, or match particulars
    """

    def __init__(self, data, types=None, index=None, subindex=None, fallback=None, kind="first"):
        super().__init__(data, types=types, index=index, fallback=fallback)
        match kind:
            case "first" | "all" | "flat" | "match":
                self._kind = kind
            case dict():
                self._kind = kind
            case _:
                raise TypeError("IterProxy bad Kind specification: ", kind, f"Recognized: first, all, flat, match")
        if self._fallback and not isinstance(self._fallback, Iterable):
            raise TypeError("Iter Proxy needs an iterable")
        self.__subindex = subindex or []
        self._kind      = kind

    def __repr__(self) -> str:
        type_str     = self._types_str()
        index_str    = ".".join(self._index())
        subindex_str = ".".join(self._subindex())
        return f"<TomlerIterProxy.{self._kind}: {index_str}:{subindex_str} ({self._fallback}) <{type_str}> >"

    def __call__(self, wrapper=None) -> TomlTypes:
        self._notify()
        wrapper = wrapper or (lambda x: x)
        match self._kind:
            case "first":
                val = self._get_first()
            case "all":
                val = self._get_all()
            case "flat":
                val = self._get_flat()
            case dict():
                val = self._get_match()
            case _:
                raise TypeError(f"Bad Kind of TomlerIterProxy: {self._kind}")

        wrapped = wrapper(val)
        return self._match_type(wrapped)

    def __iter__(self) -> Iterator[TomlTypes]:
        return iter(self())

    def _subindex(self) -> list[str]:
        return self.__subindex[:]

    def _get_first(self) -> TomlTypes:
        """
        get the first value from any available table in an array
        """
        match self._data:
            case [] | (None,):
                pass
            case [*vals]:
                for val in vals:
                    if not bool(val):
                        continue
                    return val[0]

        match self._fallback:
            case (None,):
                pass
            case None:
                return None
            case val:
                return val

        base_index = ".".join(self._index())
        sub_index = ".".join(self._subindex())
        raise TomlAccessError(f"TomlerIterProxy Failure: {base_index}[?].{sub_index}")

    def _get_all(self) -> list[TomlTypes]:
        """
        Get all matching values from array of tables
        """
        match self._data, self._fallback:
            case [] | (None,), (None,):
                pass
            case [] | (None,), val:
                return val
            case [*vals], _:
                result = []
                for val in vals:
                    result += val
                return result

        base_index = ".".join(self._index())
        sub_index = ".".join(self._subindex())
        raise TomlAccessError(f"TomlerIterProxy Failure: {base_index}[?].{sub_index}")

    def _get_flat(self) -> TomlerBase | list[TomlTypes]:
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
        raise TomlAccessError(f"TomlerIterProxy Failure: {base_index}[?].{sub_index}")

    def _get_match(self) -> TomlerBase | TomlTypes:
        """
        Get a table from an array if it matches a set of key=value pairs
        """
        for entry in self._data:
            try:
                for x in self._subindex():
                    entry = getattr(entry, x)
                if all(getattr(entry, x) == y for x,y in self._kind.items()):
                    return entry
            except TomlAccessError:
                continue

        base_index = ".".join(self._index())
        sub_index = ".".join(self._subindex())
        raise TomlAccessError(f"TomlerIterProxy Match Failure: {base_index}[?].{sub_index} != {self._match}")

    def _inject(self, val=None, attr=None, clear=None) -> TomlerIterProxy:
        new_index = self._subindex()
        if attr:
            new_index.append(attr)

        val = val or self._data
        if clear:
            val = None

        return TomlerIterProxy(val, types=self._types, fallback=self._fallback, index=self._index(), subindex=new_index, kind=self._kind)

    def _match_type(self, val:TomlTypes) -> TomlTypes:
        return val

    def _update_index(self, attr:str) -> None:
        self.__subindex.append(attr)
