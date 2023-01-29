#!/usr/bin/env python3

from .tomler import TomlAccessError, Tomler

__all__     = ["TomlAccessError", "Tomler", "load"]

__version__ = "0.1.0"

load        = Tomler.load
load_dir    = Tomler.load_dir
