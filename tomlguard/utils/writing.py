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
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports


##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

try:
    import tomli_w

    class WriterMixin:

        def __str__(self) -> str:
            return tomli_w.dumps(self._table())

        def to_file(self, path:pl.Path) -> None:
            path.write_text(str(self))

except ImportError:
    logging.debug("No Tomli-w found, TomlGuard will not write toml, only read it")

    class WriterMixin:

        def to_file(self, path:pl.Path) -> None:
            raise NotImplementedError("Tomli-w isn't installed, so TomlGuard can't write, only read")
