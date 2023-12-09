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

from tomlguard.utils.proxy import TomlGuardProxy
from tomlguard.utils.iter_proxy import TomlGuardIterProxy
from tomlguard.error import TomlAccessError

class GuardProxyEntryMixin:

    def on_fail(self, fallback:Any, types:Any|None=None) -> TomlGuardProxy:
        """
        use a fallback value in an access chain,
        eg: doot.config.on_fail("blah").this.doesnt.exist() -> "blah"

        *without* throwing a TomlAccessError
        """
        index = self._index()
        if index != ["<root>"]:
            raise TomlAccessError("On Fail not declared at entry", index)

        return TomlGuardProxy(self, types=types, fallback=fallback)

    def first_of(self, fallback:Any, types:Any|None=None) -> TomlGuardIterProxy:
        """
        get the first value from a index path, even across arrays of tables
        so instead of: data.a.b.c[0].d
        just:          data.first_of().a.b.c.d()
        """
        index = self._index()[:]

        if index != ["<root>"]:
            raise TomlAccessError("Any Of not declared at entry", index)

        return TomlGuardIterProxy(self, fallback=fallback, types=types, kind="any")

    def all_of(self, fallback:Any, types:Any|None=None) -> TomlGuardIterProxy:
        index = self._index()[:]

        if index != ["<root>"]:
            raise TomlAccessError("All Of not declared at entry", index)

        return TomlGuardIterProxy(self, fallback=fallback, kind="all")

    def flatten_on(self, fallback:Any) -> TomlGuardIterProxy:
        """
        combine all dicts at the call site to form a single dict
        """
        if not isinstance(fallback, (type(None), dict)):
            raise TypeError()

        index = self._index()

        if index != ["<root>"]:
            raise TomlAccessError("Flatten On not declared at entry", index)

        return TomlGuardIterProxy(self, fallback=fallback, kind="flat")

    def match_on(self, **kwargs:tuple[str,Any]) -> TomlGuardIterProxy:
        index = self._table()[:]
        if index != ["<root>"]:
            raise TomlAccessError("Match On not declared at entry", index)
        return TomlGuardIterProxy(self, fallback=kwargs, kind="match")
