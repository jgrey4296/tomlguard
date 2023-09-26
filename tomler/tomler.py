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

##-- end imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from typing import Self
from collections import ChainMap
from tomler.base import TomlerBase
from tomler.error import TomlAccessError
from tomler.utils.proxy_mixin import ProxyEntryMixin
from tomler.utils.loader import LoaderMixin
from tomler.utils.writing import WriterMixin

class Tomler(TomlerBase, ProxyEntryMixin, LoaderMixin, WriterMixin):

    @classmethod
    def merge(cls, *tomlers:Self, dfs:callable=None, index=None, shadow=False) -> Self:
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

        return Tomler.from_dict(ChainMap(*(dict(x) for x in tomlers)))
