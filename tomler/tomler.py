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
        self.match_type()

    def __repr__(self):
        type_str = self._types_str()
        path_str = ".".join(self._path)
        return f"<TomlerProxy: {path_str}:{type_str}>"

    def __call__(self, wrapper:callable=None):
        self._notify()
        wrapper = wrapper or (lambda x: x)
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

    def match_type(self):
        val = getattr(self, '_value')[0]
        if self._types != "Any" and not isinstance(val, self._types):
            types_str = self._types_str()
            path_str  = ".".join(self._path + ['(' + types_str + ')'])
            raise TypeError("TomlProxy Value doesn't match declared Type: ", path_str, val, self._types).with_traceback(TraceHelper()[5:10])

class TomlerIterProxy(TomlerProxy):

    def __init__(self, value=None, fallback=None, types=None, path=None, kind="any"):
        super().__init__(value or [], types=types, path=path)
        assert(kind in ["any", "all", "flat", "match"] or isinstance(kind, dict))
        self._fallback = fallback
        self._subpath  = []
        self._kind     = kind

    def __repr__(self):
        type_str = self._types_str()
        path_str = ".".join(self._path)
        subpath_str = ".".join(self._subpath)
        return f"<TomlerIterProxy.{self._kind}: {path_str}:{subpath_str} ({self._fallback}) <{type_str}> >"

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
            case "flat":
                return wrapper(self.__get_flat())
            case dict():
                return wrapper(self.__get_match())
            case _:
                raise TypeError(f"Bad Kind of TomlerIterProxy: {self._kind}")

    def __iter__(self):
        return iter(self())

    def __get_any(self):
        """
        get the key from any available table in an array
        """
        for entry in self._value[0]:
            try:
                for x in self._subpath:
                    entry = getattr(entry, x)
                match entry:
                    case TomlerProxy():
                        proxy = entry
                    case _:
                        return entry
            except TomlAccessError:
                continue

        match self._fallback:
            case None:
                pass
            case (x,):
                return x
            case _:
                return self._fallback

        base_path = ".".join(self._path)
        sub_path  = ".".join(self._subpath)
        raise TomlAccessError(f"TomlerIterProxy Failure: {base_path}[?].{sub_path}")

    def __get_all(self) -> dict|list:
        """
        Get all matching values from array of tables
        """
        all_available = []
        proxy         = None
        for entry in self._value[0]:
            try:
                for x in self._subpath:
                    entry = getattr(entry, x)
                match entry:
                    case list():
                        all_available.append(entry)
                    case dict():
                        all_available.append(entry)
                    case TomlerProxy():
                        all_available.append(entry())
                    case Tomler():
                        all_available.append(entry)
                    case _:
                        all_available.append(entry)
            except TomlAccessError:
                continue

        if not bool(all_available):
            match self._fallback:
                case None:
                    pass
                case (None,):
                    all_available.append(None)
                case (list() as vals,):
                    all_avalable += vals
                case _ as val:
                    all_available.append(val)

        return list(all_available)

    def __get_flat(self) -> Tomler:
        all_available = []
        for entry in self._value[0]:
            try:
                for x in self._subpath:
                    entry = getattr(entry, x)
                match entry:
                    case list():
                        all_available += entry
                    case dict():
                        all_available.append(entry)
                    case TomlerProxy():
                        all_available.append(entry)
                    case Tomler():
                        all_available.append(entry.get_table())
                    case _:
                        all_available.append(entry)
            except TomlAccessError:
                continue

        if not bool(all_available):
            match self._fallback:
                case None:
                    pass
                case (None,):
                    all_available.append(None)
                case _:
                    all_available.append(self._fallback)

        if not all(isinstance(x, dict) for x in all_available):
            raise ValueError("Tried to flatten on types:", [type(x) for x in all_available])

        as_dict = {}
        for x in all_available:
            as_dict.update(x.items())
        return Tomler(self._path + self._subpath, as_dict)

    def __get_match(self):
        """
        Get a table from an array if it matches a set of key=value pairs
        """
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
        raise TomlAccessError(f"TomlerIterProxy Match Failure: {base_path}[?].{sub_path} != {self._match}")

    def using(self, val):
        return TomlerIterProxy(val, types=self._types, fallback=self._fallback, path=self._path, kind=self._kind)

    def match_type(self):
        pass

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
    def read(text:str) -> self:
        logging.debug("Reading Tomler for text")
        try:
            return Tomler("<root>", toml.loads(text))
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", text, err.args) from err

    @staticmethod
    def load(*paths:str|pl.Path, mutable=False) -> self:
        logging.debug("Creating Tomler for %s", paths)
        texts = []
        for path in paths:
            texts.append(pl.Path(path).read_text())

        try:
            return Tomler("<root>", toml.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", paths, err.args) from err

    @staticmethod
    def load_dir(dirp:str|pl.Path, mutable=False) -> self:
        logging.debug("Creating Tomler for directory: %s", str(dirp))
        texts = []
        for path in pl.Path(dirp).glob("*.toml"):
            texts.append(path.read_text())

        return Tomler("<root>", toml.loads("\n".join(texts)))

    @staticmethod
    def merge(*tomlers:self) -> self:

        return Tomler()

    def report_defaulted() -> list[str]:
        """
        Report the paths using default values
        """
        return Tomler._defaulted[:]

    def __init__(self, path:pl.Path|list=None, table:dict=None, proxy:TomlerIterProxy=None, mutable:bool=False):
        assert(isinstance(proxy , (NoneType, TomlerProxy)))
        path = path if isinstance(path, list) else [path]
        super().__setattr__("__table"   , table)
        super().__setattr__("_path"     , path[:])
        super().__setattr__("__mutable" , mutable)
        super().__setattr__("__proxy"    , proxy)

    def __repr__(self):
        return f"<Tomler:{self._keys()}>"

    def __setattr__(self, attr:str, value:Any):
        if not getattr(self, "__mutable"):
            raise TypeError()
        super().__setattr__(attr, value)

    def __getattr__(self, attr:str) -> TomlerProxy | str | list | int | float | bool:
        table = getattr(self, "__table")
        proxy = getattr(self, "__proxy")
        if proxy is not None:
            getattr(proxy, attr)

        match proxy, (table.get(attr) or table.get(attr.replace("_", "-"))):
            case None, None:
                path      = getattr(self, "_path")[:]
                path_s    = ".".join(path)
                available = " ".join(self._keys())
                raise TomlAccessError(f"{path_s}.{attr} not found, available: [{available}]")
            case TomlerIterProxy(), []:
                # logging.debug("Iter []")
                return proxy.using(Tomler(path, []))
            case TomlerIterProxy(), list() as result if all(isinstance(x, dict) for x in result):
                # logging.debug("Iter, [...]")
                path     = getattr(self, "_path")[:] + [attr]
                return proxy.using([Tomler(path, x) for x in result])
            case TomlerProxy(), None:
                # logging.debug("Proxy, None")
                path     = getattr(self, "_path")[:] + [attr]
                return proxy
            case _, dict() as result:
                # logging.debug("_, {}")
                path     = getattr(self, "_path")[:]
                return Tomler(path + [attr], result, proxy=proxy)
            case None, list() as result if all(isinstance(x, dict) for x in result):
                # logging.debug("x, [{}]")
                path     = getattr(self, "_path")[:]
                return [Tomler(path + [attr], x, proxy=proxy) for x in result]
            case TomlerProxy(), _ as result:
                # logging.debug("Proxy, _")
                # Theres a fallback value, so the result needs to be wrapped so it can be called
                return proxy.using(result)
            case None, _ as result:
                # logging.debug("x, Values")
                return result

    def __call__(self):
        table    = getattr(self, "__table")
        proxy    = getattr(self, "__proxy")

        match proxy:
            case None:
                raise TomlAccessError("Calling a Tomler only work's when guarded with a proxy")
            case TomlerIterProxy() if all(isinstance(x, dict) for x in table.values()):
                return proxy.using(table.values())()
            case TomlerIterProxy():
                return proxy.using([table])()
            case TomlerProxy():
                return proxy.using(self._keys())()

    def __iter__(self):
        return iter(getattr(self, "__table").items())

    def on_fail(self, val, types=None) -> TomlerProxy:
        """
        use a fallback value in an access chain,
        eg: doot.config.on_fail("blah").this.doesnt.exist() -> "blah"

        *without* throwing a TomlAccessError
        """
        path     = getattr(self, "_path")[:]
        table    = getattr(self, "__table")
        assert(path == ["<root>"])
        return Tomler(path, table, proxy=TomlerProxy(val, types=types))

    def any_of(self, fallback=None, types=None) -> TomlerIterProxy:
        """
        get a value from a path, even across arrays of tables
        so instead of: data.a.b.c[0].d
        just:          data.any_of().a.b.c.d()
        """
        path     = getattr(self, "_path")[:]
        table    = getattr(self, "__table")
        match fallback:
            case None:
                fallback = getattr(self, "__proxy")
            case TomlerProxy():
                fallback = fallback()
            case _:
                fallback = fallback
        assert(path == ["<root>"])
        proxy = TomlerIterProxy(fallback=fallback, types=types, kind="any")
        return Tomler(path, table, proxy=proxy)

    def all_of(self, fallback=None, types=None) -> TomlerIterProxy:
        path     = getattr(self, "_path")[:]
        table    = getattr(self, "__table")
        match fallback or getattr(self, "__proxy"):
            case None:
                proxy = TomlerIterProxy(kind="all")
            case TomlerProxy():
                proxy = TomlerIterProxy(fallback=fallback(), types=types, kind="all")
            case _:
                proxy = TomlerIterProxy(fallback=fallback, types=types, kind="all")
        assert(path == ["<root>"])
        return Tomler(path, table, proxy=proxy)

    def flatten_on(self, fallback=None) -> TomlerIterProxy:
        """
        combine all dicts at the call site to form a single dict
        """
        if not isinstance(fallback, (type(None), dict)):
            raise TypeError()

        path     = getattr(self, "_path")[:]
        table    = getattr(self, "__table")
        match fallback or getattr(self, "__proxy"):
            case None:
                fallback = {}
            case TomlerProxy() as proxy:
                fallback = proxy()
            case _:
                pass

        assert(path == ["<root>"])
        proxy = TomlerIterProxy(fallback=fallback, kind="flat")
        return Tomler(path, table, proxy=proxy)

    def match_on(self, **kwargs) -> TomlerIterProxy:
        table = getattr(self, "__table")
        path  = getattr(self, "_path")[:]
        assert(path == ["<root>"])
        proxy = TomlerIterProxy(fallback=kwargs, kind="match")
        return Tomler(path, table, proxy=proxy)

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
