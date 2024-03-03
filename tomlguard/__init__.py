#!/usr/bin/env python3

from typing import Final

from .tomlguard import TomlAccessError, TomlGuard
from .base   import TomlTypes

__all__     = ["TomlAccessError", "TomlGuard", "load"]

__version__ : Final[str] = "0.3.0"

load        = TomlGuard.load
load_dir    = TomlGuard.load_dir
read        = TomlGuard.read
