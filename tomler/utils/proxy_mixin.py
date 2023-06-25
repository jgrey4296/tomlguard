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

from tomler.utils.proxy import TomlerProxy
from tomler.utils.iter_proxy import TomlerIterProxy
from tomler.error import TomlAccessError

class ProxyEntryMixin:

    def on_fail(self, fallback, types=None) -> TomlerProxy:
        """
        use a fallback value in an access chain,
        eg: doot.config.on_fail("blah").this.doesnt.exist() -> "blah"

        *without* throwing a TomlAccessError
        """
        index = self._index()
        if index != ["<root>"]:
            raise TomlAccessError("On Fail not declared at entry", index)

        return TomlerProxy(self, types=types, index=index, fallback=fallback)

    def first_of(self, fallback, types=None) -> TomlerIterProxy:
        """
        get the first value from a index path, even across arrays of tables
        so instead of: data.a.b.c[0].d
        just:          data.first_of().a.b.c.d()
        """
        index = self._index()[:]

        if index != ["<root>"]:
            raise TomlAccessError("Any Of not declared at entry", index)

        return TomlerIterProxy(self, fallback=fallback, types=types, kind="any")

    def all_of(self, fallback, types=None) -> TomlerIterProxy:
        index = self._index()[:]

        if index != ["<root>"]:
            raise TomlAccessError("All Of not declared at entry", index)

        return TomlerIterProxy(self, fallback=fallback, index=index, kind="all")

    def flatten_on(self, fallback) -> TomlerIterProxy:
        """
        combine all dicts at the call site to form a single dict
        """
        if not isinstance(fallback, (type(None), dict)):
            raise TypeError()

        index = self._index()

        if index != ["<root>"]:
            raise TomlAccessError("Flatten On not declared at entry", index)

        return TomlerIterProxy(self, index=index, fallback=fallback, kind="flat")

    def match_on(self, **kwargs) -> TomlerIterProxy:
        index = self._table()[:]
        if index != ["<root>"]:
            raise TomlAccessError("Match On not declared at entry", index)
        return TomlerIterProxy(self, index=index, fallback=kwargs, kind="match")