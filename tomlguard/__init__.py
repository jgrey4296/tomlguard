#!/usr/bin/env python3

from typing import Final, TypeAlias
import datetime
from collections import ChainMap

__all__     = ["TomlAccessError", "TomlGuard", "load"]

__version__ : Final[str] = "0.4.0"

TomlTypes : TypeAlias = str | int | float | bool | list['TomlTypes'] | dict[str,'TomlTypes'] | datetime.datetime
TGDict    : TypeAlias = dict | ChainMap

from .tomlguard import TomlAccessError, TomlGuard

load        = TomlGuard.load
load_dir    = TomlGuard.load_dir
read        = TomlGuard.read
