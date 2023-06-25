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

from types import UnionType
from tomler.utils.trace_helper import TraceHelper
from tomler.base import TomlerBase
from tomler.error import TomlAccessError

class TomlerProxy:
    """
    A Wrapper for guarded access to toml values.
    you get the value by calling it.
    Until then, it tracks attribute access,
    and reports that to TomlerBase when called.
    It also can type check its value and the value retrieved from the toml data
    """

    def __init__(self, data, types=None, index=None, fallback=None):
        self._types             = types or Any
        self._data : TomlerBase = data
        self.__index            = index or ["<root>"]
        self._fallback          = fallback
        if fallback:
            self._match_type(fallback)

    def __repr__(self):
        type_str = self._types_str()
        index_str = ".".join(self._index())
        return f"<TomlerProxy: {index_str}:{type_str}>"

    def __call__(self, wrapper:callable=None):
        self._notify()
        wrapper = wrapper or (lambda x: x)
        match self._data, self._fallback:
            case TomlerBase(), _:
                val = self._data
            case (None,), None:
                raise ValueError("No Value, and no fallback")
            case (None,), data:
                val = data
            case None, _:
                val = None
            case TomlerBase() as data, _:
                val = dict(data)
            case _ as data, _:
                val = data

        wrapped = wrapper(val)
        return self._match_type(wrapped)

    def __getattr__(self, attr):
        try:
            match self._data:
                case TomlerBase():
                    return self._inject(self._data[attr], attr=attr)
                case None:
                    raise TomlAccessError()
                case _:
                    return self._inject(attr=attr)
        except TomlAccessError as err:
            return self._inject(clear=True, attr=attr)

    def __getitem__(self, keys):
        curr = self
        match keys:
            case tuple():
                for key in keys:
                    curr = curr.__getattr__(key)
            case str():
                curr = self.__getattr__(keys)

        return curr

    def __len__(self) -> int:
        if hasattr(self._data, "__len__"):
            return len(self._data)

        return 0

    def __bool__(self):
        return self._data is not None

    def _notify(self):
        types_str = self._types_str()
        match self._data, self._fallback, self._index():
            case TomlerBase(), _, _:
                pass
            case _, _, []:
                pass
            case (None,), val, [*index]:
                TomlerBase.add_defaulted(".".join(index), val, types_str)
            case val, _, [*index]:
                TomlerBase.add_defaulted(".".join(index), val, types_str)
            case val, flbck, index,:
                raise TypeError("Unexpected Values found: ", val, index, flbck)

    def _types_str(self):
        match self._types:
            case UnionType() as targ:
                types_str = repr(targ)
            case type(__name__=targ):
                types_str = targ
            case _ as targ:
                types_str = str(targ)

        return types_str

    def _inject(self, val=(None,), attr=None, clear=False) -> TomlerProxy:
        new_index = self._index()
        if attr:
            new_index.append(attr)

        match val:
            case (None,):
                val = self._data
            case _:
                pass

        if clear:
            val = (None,)
        return TomlerProxy(val, types=self._types, index=new_index, fallback=self._fallback)

    def _match_type(self, val) -> Any:
        if self._types != Any and not isinstance(val, self._types):
            types_str = self._types_str()
            index_str  = ".".join(self.__index + ['(' + types_str + ')'])
            err = TypeError("TomlProxy Value doesn't match declared Type: ", index_str, val, self._types)
            raise err.with_traceback(TraceHelper()[5:10])

        return val

    def _index(self):
        return self.__index[:]

    def _update_index(self, attr):
        self.__index.append(attr)
