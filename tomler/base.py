
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

from types import NoneType
from collections.abc import Mapping
from tomler.error import TomlAccessError

super_get = object.__getattribute__
super_set = object.__setattr__

class TomlerBase(Mapping):
    """
    Provides access to toml data (Tomler.load(apath))
    but as attributes (data.a.path.in.the.data)
    instead of key access (data['a']['path']['in']['the']['data'])

    while also providing typed, guarded access:
    data.on_fail("test", str | int).a.path.that.may.exist()

    while it can then report missing paths:
    data.report_defaulted() -> ['a.path.that.may.exist.<str|int>']
    """

    _defaulted : ClassVar[set[str]] = set()

    @staticmethod
    def add_defaulted(index:str, val:Any, types:str="Any"):
        match index, val:
            case list(), _:
                raise TypeError("Tried to Register a default value with a list index, use a str")
            case _, bool():
                index_str = f"{index} = {str(val).lower()} # <{types}>"
            case _, val:
                index_str = f"{index} = {repr(val)} # <{types}>"
            case val, _, [*index]:
                index_str = f"{index} = {repr(val)} # <{types}>"
            case val, index:
                raise TypeError("Unexpected Values found: ", val, index)

        TomlerBase._defaulted.add(index_str)

    @staticmethod
    def report_defaulted() -> list[str]:
        """
        Report the index paths inject default values
        """
        return list(TomlerBase._defaulted)

    def __init__(self, data:dict, index:None|list=None, mutable:bool=False):
        super_set(self, "__table", data or {})
        super_set(self, "__index"   , (index or ["<root>"])[:])
        super_set(self, "__mutable" , mutable)

    def __repr__(self):
        return f"<Tomler:{self.keys()}>"

    def __setattr__(self, attr:str, value:Any):
        if not getattr(self, "__mutable"):
            raise TypeError()
        super_set(self, attr, value)

    def __getattr__(self, attr:str) -> TomlerBase | str | list | int | float | bool:
        table = self._table()

        if attr not in table and attr.replace("_", "-") not in table:
            index     = self._index()
            index_s   = ".".join(index)
            available = " ".join(self.keys())
            raise TomlAccessError(f"{index_s} not found, available: [{available}]")

        match table.get(attr, None) or table.get(attr.replace("_", "-"), None):
            case dict() as result:
                return self.__class__(result, self._index() + [attr])
            case list() as result if all(isinstance(x, dict) for x in result):
                index = self._index()
                return [self.__class__(x, index[:]) for x in result]
            case _ as result:
                return result

    def __getitem__(self, keys):
        curr = self
        match keys:
            case tuple():
                for key in keys:
                    curr = curr.__getattr__(key)
            case str():
                curr = self.__getattr__(keys)

        return curr

    def __len__(self):
        return len(self._table())

    def __call__(self):
        raise TomlAccessError("Don't call a Tomler, call a TomlerProxy")

    def __iter__(self):
        return iter(getattr(self, "__table").items())

    def __contains__(self, other):
        return other in self.keys()

    def _index(self):
        return super_get(self, "__index")[:]

    def _table(self):
        return super_get(self, "__table")

    def get(self, key, default=None) -> Any:
        if key in self:
            return self[key]

        return default

    def keys(self):
        # table  = object.__getattribute__(self, "__table")
        table = super_get(self, "__table")
        return list(table.keys())

    def items(self):
        # match object.__getattribute__(self, "__table"):
        match super_get(self, "__table"):
            case dict() as val:
                return val.items()
            case list() as val:
                return zip(val, val)
            case _:
                raise TypeError()

    def values(self):
        # match object.__getattribute__(self, "__table"):
        match super_get(self, "__table"):
            case dict() as val:
                return val.values()
            case list() as val:
                return val
            case _:
                raise TypeError()
