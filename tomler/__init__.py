#!/usr/bin/env python3

from typing import Final

from .tomler import TomlAccessError, Tomler
from .base   import TomlTypes

__all__     = ["TomlAccessError", "Tomler", "load"]

__version__ : Final[str] = "0.1.0"

load        = Tomler.load
load_dir    = Tomler.load_dir
read        = Tomler.read
