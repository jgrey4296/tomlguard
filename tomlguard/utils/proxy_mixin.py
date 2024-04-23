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

from tomlguard.utils.failure_proxy import TomlGuardFailureProxy
from tomlguard.error import TomlAccessError

class GuardProxyEntryMixin:
    """ A Mixin to add to GuardBase.
    enables handling a number of conditions when accessing values in the underlying data.
    eg:
    tg.on_fail(2, int).a.value() # either get a.value, or 2. whichever returns has to be an int.
    """

    def on_fail(self, fallback:Any, types:Any|None=None, non_root=False) -> TomlGuardFailureProxy:
        """
        use a fallback value in an access chain,
        eg: doot.config.on_fail("blah").this.doesnt.exist() -> "blah"

        *without* throwing a TomlAccessError
        """
        index = self._index()
        if index != ["<root>"] and not non_root:
            raise TomlAccessError("On Fail not declared at entry", index)

        return TomlGuardFailureProxy(self, types=types, fallback=fallback)

    def first_of(self, fallback:Any, types:Any|None=None) -> TomlGuardIterProxy:
        """
        get the first non-None value from a index path, even across arrays of tables
        so instead of: data.a.b.c[0].d
        just:          data.first_of().a.b.c.d()
        """
        raise NotImplementedError()

    def all_of(self, fallback:Any, types:Any|None=None) -> TomlGuardIterProxy:
        raise NotImplementedError()

    def flatten_on(self, fallback:Any) -> TomlGuardIterProxy:
        """
        combine all dicts at the call site to form a single dict
        """
        raise NotImplementedError()

    def match_on(self, **kwargs:tuple[str,Any]) -> TomlGuardIterProxy:
        raise NotImplementedError()
