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

from tomler.base import TomlerBase


class LoaderMixin:

    @staticmethod
    def read(text:str) -> self:
        logging.debug("Reading Tomler for text")
        try:
            return TomlerBase(toml.loads(text))
        except Exception as err:
            raise IOError("TomlerBase Failed to Load: ", text, err.args) from err

    @staticmethod
    def from_dict(data:dict) -> self:
        logging.debug("Making Tomler from dict")
        try:
            return TomlerBase(data)
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", data, err.args) from err

    @staticmethod
    def load(*paths:str|pl.Path) -> self:
        logging.debug("Creating Tomler for %s", paths)
        try:
            texts = []
            for path in paths:
                texts.append(pl.Path(path).read_text())

            return TomlerBase(toml.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("TomlerBase Failed to Load: ", paths, err.args) from err

    @staticmethod
    def load_dir(dirp:str|pl.Path) -> self:
        logging.debug("Creating Tomler for directory: %s", str(dirp))
        try:
            texts = []
            for path in pl.Path(dirp).glob("*.toml"):
                texts.append(path.read_text())

            return TomlerBase(toml.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("Tomler Failed to Directory: ", dirp, err.args) from err
