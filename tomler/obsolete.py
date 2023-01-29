#/usr/bin/env python3
"""

"""
##-- imports
from __future__ import annotations

import os
import pathlib as pl
from importlib.resources import files
from instal.util.toml_accessor import TomlAccessError, TomlAccessor

##-- end imports

default_toml  = files("instal.__data") / "defaults.toml"

__loaded_toml = toml.loads(default_toml.read_text())['tool']['instal']

def __getattr__(attr):
    result = __loaded_toml.get(attr)
    if result is None:
        raise TomlAccessError(attr)

    if isinstance(result, dict):
        return TomlAccessor(attr, result)

    return result

def __dir__():
    return list(__loaded_toml.keys())

def set_defaults(path: pl.Path):
    global __loaded_toml
    __loaded_toml = toml.loads(path.read_text())['tool']['instal']
