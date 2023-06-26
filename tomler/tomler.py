#/usr/bin/env python3
"""
Utility classes for attribute based access to loaded toml data,
simplifying data['blah']['awe']['awg']
to data.blah.awe.awg

Also allows guarded access:
result = data.on_fail('fallback').somewhere.along.this.doesnt.exist()
restul equals "fallback" or whatever `exist` is.

Python access model (simplified):
object.__getattribute(self, name):
    try:
        return self.__dict__[name]
    except AttributeError:
        return self.__getattr__(name)

So by looking up values in Tomler.__table and handling missing values,
we can skip dict style key access

"""
##-- imports
from __future__ import annotations

import abc
import logging as logmod
import pathlib as pl
from types import NoneType
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from re import Pattern
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref

try:
    # For py 3.11 onwards:
    import tomllib as toml
except ImportError:
    # Fallback to external package
    import toml

if TYPE_CHECKING:
    # tc only imports
    pass
##-- end imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from collections import ChainMap
from tomler.utils.proxy_mixin import ProxyEntryMixin
from tomler.base import TomlerBase
from tomler.error import TomlAccessError

class LoaderMixin:

    @staticmethod
    def read(text:str) -> self:
        logging.debug("Reading Tomler for text")
        try:
            return Tomler(toml.loads(text))
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", text, err.args) from err

    @staticmethod
    def from_dict(data:dict) -> self:
        logging.debug("Making Tomler from dict")
        try:
            return Tomler(data)
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", data, err.args) from err

    @staticmethod
    def load(*paths:str|pl.Path) -> self:
        logging.debug("Creating Tomler for %s", paths)
        try:
            texts = []
            for path in paths:
                texts.append(pl.Path(path).read_text())

            return Tomler(toml.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", paths, err.args) from err

    @staticmethod
    def load_dir(dirp:str|pl.Path) -> self:
        logging.debug("Creating Tomler for directory: %s", str(dirp))
        try:
            texts = []
            for path in pl.Path(dirp).glob("*.toml"):
                texts.append(path.read_text())

            return Tomler(toml.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("Tomler Failed to Directory: ", dirp, err.args) from err

class Tomler(TomlerBase, ProxyEntryMixin, LoaderMixin):

    @staticmethod
    def merge(*tomlers:self, dfs:callable=None, index=None, shadow=False) -> self:
        """
        Given an ordered list of tomlers, convert them to dicts,
        update an empty dict with each,
        then wrap that combined dict in a tomler
        # TODO if given a dfs callable, use it to merge more intelligently
        """
        curr_keys = set()
        for data in tomlers:
            new_keys = set(data.keys())
            if bool(curr_keys & new_keys) and not shadow:
                raise KeyError("Key Conflict:", curr_keys & new_keys)
            curr_keys |= new_keys

        return Tomler.from_dict(ChainMap(*tomlers))
