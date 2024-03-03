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

So by looking up values in TomlGuard.__table and handling missing values,
we can skip dict style key access

"""
##-- imports
from __future__ import annotations

import abc
import logging as logmod
import pathlib as pl
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from re import Pattern
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref

try:
    # for py 3.10 onwards:
    from typing import TypeAlias
except ImportError:
    TypeAlias = Any

try:
    # for py 3.11 onwards:
    from typing import Self
except ImportError:
    Self = Any

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

from collections import ChainMap
from tomlguard.base import GuardBase
from tomlguard.error import TomlAccessError
from tomlguard.utils.proxy_mixin import GuardProxyEntryMixin
from tomlguard.utils.loader import LoaderMixin
from tomlguard.utils.writing import WriterMixin

class TomlGuard(GuardBase, GuardProxyEntryMixin, LoaderMixin, WriterMixin):

    @classmethod
    def merge(cls, *tomlguards:Self, dfs:callable=None, index=None, shadow=False) -> Self:
        """
        Given an ordered list of tomlguards, convert them to dicts,
        update an empty dict with each,
        then wrap that combined dict in a tomlguard
        # TODO if given a dfs callable, use it to merge more intelligently
        """
        curr_keys = set()
        for data in tomlguards:
            new_keys = set(data.keys())
            if bool(curr_keys & new_keys) and not shadow:
                raise KeyError("Key Conflict:", curr_keys & new_keys)
            curr_keys |= new_keys

        return TomlGuard.from_dict(ChainMap(*(dict(x) for x in tomlguards)))

    def remove_prefix(self, prefix) -> TomlGuard:
        """ Try to remove a prefix from loaded data
          eg: TomlGuard(tools.tomlguard.data..).remove_prefix("tools.tomlguard")
          -> TomlGuard(data..)
        """
        match prefix:
            case None:
                return self
            case str():
                logging.debug("Removing prefix from data: %s", prefix)
                try:
                    attempt = self
                    for x in prefix.split("."):
                        attempt = attempt[x]
                    else:
                        return TomlGuard(attempt)
                except TomlAccessError:
                    return self
