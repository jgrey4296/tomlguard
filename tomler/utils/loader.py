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


##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from typing import Self
from tomler.base import TomlTypes
from tomler.error import TomlAccessError

try:
    # For py 3.11 onwards:
    import tomllib as toml
except ImportError:
    # Fallback to external package
    import toml

class LoaderMixin:

    @classmethod
    def read(cls, text:str) -> Self:
        logging.debug("Reading Tomler for text")
        try:
            return cls(toml.loads(text))
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", text, err.args) from err

    @classmethod
    def from_dict(cls, data:dict[str, TomlTypes]) -> Self:
        logging.debug("Making Tomler from dict")
        try:
            return cls(data)
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", data, err.args) from err

    @classmethod
    def load(cls, *paths:str|pl.Path) -> Self:
        logging.debug("Creating Tomler for %s", paths)
        try:
            texts = []
            for path in paths:
                texts.append(pl.Path(path).read_text())

            return cls(toml.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", paths, err.args) from err

    @classmethod
    def load_dir(cls, dirp:str|pl.Path) -> Self:
        logging.debug("Creating Tomler for directory: %s", str(dirp))
        try:
            texts = []
            for path in pl.Path(dirp).glob("*.toml"):
                texts.append(path.read_text())

            return cls(toml.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("Tomler Failed to Directory: ", dirp, err.args) from err
