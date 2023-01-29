#/usr/bin/env python3
"""
Utility classes for attribute based access to loaded toml data,
simplifying data['blah']['awe']['awg']
to data.blah.awe.awg

Also allows guarded access:
result = data.on_fail('fallback').somewhere.along.this.doesnt.exist()
restul equals "fallback" or whatever `exist` is.

"""
##-- imports
from __future__ import annotations

import abc
import logging as logmod
import pathlib as pl
from types import NoneType
from copy import deepcopy
from dataclasses import InitVar, dataclass, field
from re import Pattern
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable)
from types import UnionType
from uuid import UUID, uuid1
from weakref import ref

try:
    # For py 3.11 onwards:
    import tomllib as toml
except ImportError:
    # Fallback to external package
    import toml

if TYPE_CHECKING:
    # tc only imports
    pass
##-- end imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from tomler.utils.trace_helper import TraceHelper

class TomlAccessError(AttributeError):
    pass

class TomlerProxy:
    """
    A Wrapper for guarded access to toml values.
    you get the value by calling it.
    Until then, it tracks attribute access,
    and reports that to Tomler when called.
    It also can type check its value and the value retrieved from the toml data
    """

    def __init__(self, value, types=None, path=None):
        types = types or "Any"
        self._value = (value,)
        self._types = types
        self._path  = path or []

        if self._types != "Any" and not isinstance(value, self._types):
            types_str = self._types_str()
            path_str = ".".join(self._path + ['(' + types_str + ')'])
            raise TypeError("Toml Value doesn't match declared Type: ", path_str, self._value, self._types).with_traceback(TraceHelper()[5:10])

    def __repr__(self):
        type_str = self._types_str()
        path_str = ".".join(self._path)
        return f"<TomlerProxy: {path_str}:{type_str}>"

    def __call__(self, wrapper:callable=None):
        self._notify()
        wrapper   = wrapper or (lambda x: x)
        return wrapper(self._value[0])

    def __getattr__(self, attr):
        self._path.append(attr)
        return self

    def _notify(self):
        types_str = self._types_str()
        match self._value, self._path:
            case (val,), []:
                return
            case (str() as val,), [*path]:
                path_str = ".".join(path) + f"   =  \"{val}\" # <{types_str}>"
                Tomler._defaulted.append(path_str)
                return
            case (bool() as val,), [*path]:
                path_str = ".".join(path) + f"   =  {str(val).lower()} # <{types_str}>"
                Tomler._defaulted.append(path_str)
                return
            case (val,), [*path]:
                path_str = ".".join(path) + f"   =  {val} # <{types_str}>"
                Tomler._defaulted.append(path_str)
                return
            case val, path:
                raise TypeError("Unexpected Values found: ", val, path)

    def _types_str(self):
        match self._types:
            case UnionType() as targ:
                types_str = repr(targ)
            case type(__name__=targ):
                types_str = targ
            case _ as targ:
                types_str = str(targ)

        return types_str

    def using(self, val):
        return TomlerProxy(val, types=self._types, path=self._path)

class TomlerIterProxy(TomlerProxy):

    def __init__(self, value, types=None, path=None, kind="any"):
        super().__init__(value, types=types, path=path)
        assert(kind in ["any", "all"] or isinstance(kind, dict))
        self._subpath = []
        self._kind    = kind

    def __repr__(self):
        type_str = self._types_str()
        path_str = ".".join(self._path)
        return f"<TomlerIterProxy: {path_str}:{type_str}>"

    def __getattr__(self, attr):
        self._subpath.append(attr)
        return self

    def __call__(self, wrapper=None):
        wrapper = wrapper or (lambda x: x)
        match self._kind:
            case "any":
                return wrapper(self.__get_any())
            case "all":
                return wrapper(self.__get_all())
            case dict():
                return wrapper(self.__get_match())
            case _:
                raise TypeError(f"Bad Kind of TomlerIterProxy: {self._kind}")

    def __get_any(self):
        for entry in self._value[0]:
            try:
                for x in self._subpath:
                    entry = getattr(entry, x)
                return entry
            except TomlAccessError:
                continue
        base_path = ".".join(self._path)
        sub_path  = ".".join(self._subpath)
        raise TomlAccessError(f"IterProxy Failure: {base_path}[?].{sub_path}")

    def __get_all(self) -> dict|list:
        all_available = []
        for entry in self._value[0]:
            try:
                for x in self._subpath:
                    entry = getattr(entry, x)
                match entry:
                    case list():
                        all_available += entry
                    case _:
                        all_available.append(entry)
            except TomlAccessError:
                continue

        if all(isinstance(x, Tomler) for x in all_available):
            as_dict = {}
            for x in all_available:
                as_dict.update(x.items())
            return Tomler(self._path + self._subpath, as_dict)

        return all_available

    def __get_match(self):
        for entry in self._value[0]:
            try:
                for x in self._subpath:
                    entry = getattr(entry, x)
                if all(getattr(entry, x) == y for x,y in self._kind.items()):
                    return entry
            except TomlAccessError:
                continue
        base_path = ".".join(self._path)
        sub_path  = ".".join(self._subpath)
        raise TomlAccessError(f"IterProxy Match Failure: {base_path}[?].{sub_path} != {self._match}")

class Tomler:
    """
    Provides access to toml data (Tomler.load(apath))
    but as attributes (data.a.path.in.the.data)
    instead of key access (data['a']['path']['in']['the']['data'])

    while also providing typed, guarded access:
    data.on_fail("test", str | int).a.path.that.may.exist()

    while it can then report missing paths:
    data._report() -> ['a.path.that.may.exist.<str|int>']
    """

    _defaulted : ClassVar[list[str]] = []

    @staticmethod
    def load(*paths:str|pl.Path, mutable=False) -> self:
        logging.info("Creating Tomler for %s", paths)
        texts = []
        for path in paths:
            texts.append(pl.Path(path).read_text())

        return Tomler("<root>", toml.loads("\n".join(texts)))

    @staticmethod
    def load_dir(dirp:str|pl.Path, mutable=False) -> self:
        logging.info("Creating Tomler for directory: %s", str(dirp))
        texts = []
        for path in pl.Path(dirp).glob("*.toml"):
            texts.append(path.read_text())

        return Tomler("<root>", toml.loads("\n".join(texts)))

    def report_defaulted() -> list[str]:
        """
        Report the paths using default values
        """
        return Tomler._defaulted[:]

    def __init__(self, path=None, table=None, fallback=None, mutable=False, iterproxy=False):
        assert(isinstance(fallback, (NoneType, TomlerProxy)))
        path = path if isinstance(path, list) else [path]
        super().__setattr__("__table"     , table)
        super().__setattr__("_path"       , path[:])
        super().__setattr__("__fallback"  , fallback)
        super().__setattr__("__mutable"   , mutable)
        super().__setattr__("__iterproxy" , iterproxy)

    def __repr__(self):
        return f"<Tomler:{self._keys()}>"

    def __setattr__(self, attr, value):
        if not getattr(self, "__mutable"):
            raise TypeError()
        super().__setattr__(attr, value)

    def __getattr__(self, attr) -> TomlerProxy | str | list | int | float | bool:
        table     = getattr(self, "__table")
        fallback  = getattr(self, "__fallback")
        iterproxy = getattr(self, "__iterproxy")
        if fallback:
            getattr(fallback, attr)
        match (table.get(attr) or table.get(attr.replace("_", "-"))):
            case None if fallback is not None:
                return fallback
            case None:
                path     = getattr(self, "_path")[:]
                path_s    = ".".join(path)
                available = " ".join(self._keys())
                raise TomlAccessError(f"{path_s}.{attr} not found, available: [{available}]")
            case dict() as result:
                path     = getattr(self, "_path")[:]
                return Tomler(path + [attr], result, fallback=fallback)
            case list() as result if all(isinstance(x, dict) for x in result) and bool(iterproxy):
                path     = getattr(self, "_path")[:] + [attr]
                return TomlerIterProxy([Tomler(path, x, fallback=fallback) for x in result], path=path, kind=iterproxy)
            case list() as result if all(isinstance(x, dict) for x in result):
                path     = getattr(self, "_path")[:]
                return [Tomler(path + [attr], x, fallback=fallback) for x in result]
            case _ as result if fallback is not None:
                # Theres a fallback value, so the result needs to be wrapped so it can be called
                return fallback.using(result)
            case _ as result:
                return result

    def __call__(self):
        table    = getattr(self, "__table")
        fallback = getattr(self, "__fallback")
        if fallback is None:
            raise TomlAccessError("Calling a Tomler only work's when guarded with on_fail")

        return fallback.using(self._keys())()

    def __iter__(self):
        return iter(getattr(self, "__table"))

    def on_fail(self, val, types=None) -> TomlerProxy:
        """
        use a fallback value in an access chain,
        eg: doot.config.on_fail("blah").this.doesnt.exist() -> "blah"

        *without* throwing a TomlAccessError
        """
        path  = getattr(self, "_path")[:]
        table = getattr(self, "__table")
        assert(path == ["<root>"])
        return Tomler(path, table, fallback=TomlerProxy(val, types=types))

    def any_of(self):
        path  = getattr(self, "_path")[:]
        table = getattr(self, "__table")
        assert(path == ["<root>"])
        return Tomler(path, table, iterproxy="any")

    def all_of(self):
        path  = getattr(self, "_path")[:]
        table = getattr(self, "__table")
        assert(path == ["<root>"])
        return Tomler(path, table, iterproxy="all")

    def match_on(self, **kwargs):
        table = getattr(self, "__table")
        path  = getattr(self, "_path")[:]
        assert(path == ["<root>"])
        return Tomler(path, table, iterproxy=kwargs)

    def _keys(self):
        table  = object.__getattribute__(self, "__table")
        return list(table.keys())

    def _items(self):
        match object.__getattribute__(self, "__table"):
            case dict() as val:
                return val.items()
            case list() as val:
                return zip(val, val)
            case _:
                raise TypeError()

    def _values(self):
        match object.__getattribute__(self, "__table"):
            case dict() as val:
                return val.values()
            case list() as val:
                return val
            case _:
                raise TypeError()

    def get_table(self):
        return getattr(self, "__table")
