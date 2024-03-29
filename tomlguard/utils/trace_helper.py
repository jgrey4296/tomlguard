#!/usr/bin/env python3
"""

"""
##-- imports

##-- end imports

##-- default imports
from __future__ import annotations

import types
import abc
import datetime
import sys
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeVar,
                    cast, final, overload, runtime_checkable)
from uuid import UUID, uuid1
from weakref import ref

##-- end default imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class TraceHelper:
    """
    Build Stack Traces with more control
    """

    def __init__(self):
        self.frames = []
        self.get_frames()

    def __getitem__(self, val=None):
        match val:
            case None:
                return self.to_tb()
            case slice() | int():
                return self.to_tb(self.frames[val])
            case _:
                raise TypeError("Bad value passed to TraceHelper")

    def get_frames(self):
        """ from https://stackoverflow.com/questions/27138440 """
        tb    = None
        depth = 0
        while True:
            try:
                frame = sys._getframe(depth)
                depth += 1
            except ValueError as exc:
                break

            self.frames.append(frame)

    def to_tb(self, frames=None):
        top = None
        frames = frames or self.frames
        for frame in frames:
            top = types.TracebackType(top, frame,
                                     frame.f_lasti,
                                     frame.f_lineno)
        return top
