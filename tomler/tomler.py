#/usr/bin/env python3
"""
Utility classes for attribute based access to loaded toml data,
simplifying data['blah']['awe']['awg']
to data.blah.awe.awg

Also allows guarded access:
result = data.on_fail('fallback').somewhere.along.this.doesnt.exist()
restul equals "fallback" or whatever `exist` is.

Python access model (simplified):
object.__getattribute(self, name):
    try:
        return self.__dict__[name]
    except AttributeError:
        return self.__getattr__(name)

So by looking up values in Tomler.__table and handling missing values,
we can skip dict style key access

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

from collections import ChainMap
from tomler.utils.trace_helper import TraceHelper

super_get = object.__getattribute__
super_set = object.__setattr__

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

    def __init__(self, value, types=None, index=None):
        types = types or "Any"
        self._value = (value,)
        self._types = types
        self.__index  = (index or ["<root>"])
        self._match_type()

    def __repr__(self):
        type_str = self._types_str()
        index_str = ".".join(self._index())
        return f"<TomlerProxy: {index_str}:{type_str}>"

    def __call__(self, wrapper:callable=None):
        self._notify()
        wrapper = wrapper or (lambda x: x)
        return wrapper(self._value[0])

    def __getattr__(self, attr):
        self.update_index(attr)
        return self

    def __getitem__(self, keys):
        curr = self
        match keys:
            case tuple():
                for key in keys:
                    curr = curr.__getattr__(key)
            case str():
                curr = self.__getattr__(keys)

        return curr

    def _notify(self):
        types_str = self._types_str()
        match self._value, self._index():
            case (val,), []:
                return
            case (str() as val,), [*index]:
                index_str = ".".join(index) + f" = \"{val}\" # <{types_str}>"
                Tomler._defaulted.append(index_str)
                return
            case (bool() as val,), [*index]:
                index_str = ".".join(index) + f" = {str(val).lower()} # <{types_str}>"
                Tomler._defaulted.append(index_str)
                return
            case (val,), [*index]:
                index_str = ".".join(index) + f" = {val} # <{types_str}>"
                Tomler._defaulted.append(index_str)
                return
            case val, index:
                raise TypeError("Unexpected Values found: ", val, index)

    def _types_str(self):
        match self._types:
            case UnionType() as targ:
                types_str = repr(targ)
            case type(__name__=targ):
                types_str = targ
            case _ as targ:
                types_str = str(targ)

        return types_str

    def inject(self, val=None, attr=None) -> TomlerProxy:
        new_index = self._index()
        if attr:
            new_index.append(attr)
        return TomlerProxy(val or self._value[0], types=self._types, index=new_index)

    def _match_type(self):
        val = getattr(self, '_value')[0]
        if self._types != "Any" and not isinstance(val, self._types):
            types_str = self._types_str()
            index_str  = ".".join(self.__index + ['(' + types_str + ')'])
            raise TypeError("TomlProxy Value doesn't match declared Type: ", index_str, val, self._types).with_traceback(TraceHelper()[5:10])

    def _index(self):
        return self.__index[:]

    def update_index(self, attr):
        self.__index.append(attr)

class TomlerIterProxy(TomlerProxy):
    """
    A Proxy for lists and dicts, which can flatten, or match particulars
    """

    def __init__(self, value=None, fallback=None, types=None, index=None, kind="first"):
        super().__init__(value or [], types=types, index=index)
        match kind:
            case "first" | "all" | "flat" | "match":
                self._kind = kind
            case dict():
                self._kind = kind
            case _:
                raise TypeError("IterProxy bad Kind specification: ", kind)
        if not isinstance(self._value[0], Iterable):
            raise TypeError("Iter Proxy needs an iterable")
        self._fallback  = fallback
        self.__subindex = []
        self._kind      = kind

    def __repr__(self):
        type_str     = self._types_str()
        index_str    = ".".join(self._index())
        subindex_str = ".".join(self._subindex())
        return f"<TomlerIterProxy.{self._kind}: {index_str}:{subindex_str} ({self._fallback}) <{type_str}> >"

    def __call__(self, wrapper=None):
        wrapper = wrapper or (lambda x: x)
        match self._kind:
            case "first":
                return wrapper(self._get_first())
            case "all":
                return wrapper(self._get_all())
            case "flat":
                return wrapper(self._get_flat())
            case dict():
                return wrapper(self._get_match())
            case _:
                raise TypeError(f"Bad Kind of TomlerIterProxy: {self._kind}")

    def __iter__(self):
        return iter(self())

    def _subindex(self):
        return self.__subindex[:]

    def _get_first(self):
        """
        get the first value from any available table in an array
        """
        for entry in self._value[0]:
            try:
                match entry() if isinstance(entry, TomlerProxy) else entry:
                    case [val]:
                        return val
                    case [val, *vals]:
                        return val

            except TomlAccessError:
                continue

        match self._fallback:
            case None:
                pass
            case (x,):
                return x
            case _:
                return self._fallback

        base_index = ".".join(self._index())
        sub_index = ".".join(self._subindex())
        raise TomlAccessError(f"TomlerIterProxy Failure: {base_index}[?].{sub_index}")

    def _get_all(self) -> list:
        """
        Get all matching values from array of tables
        """
        all_available = []
        for entry in self._value[0]:
            try:
                match entry() if isinstance(entry, TomlerProxy) else entry:
                    case None:
                        pass
                    case list() as val if bool(val):
                        all_available.append(entry)
                    case dict():
                        all_available.append(entry)
                    case Tomler():
                        all_available.append(entry)
                    case _:
                        all_available.append(entry)
            except TomlAccessError:
                continue

        if bool(all_available):
            return all_available

        match self._fallback:
            case None:
                pass
            case (None,):
                return None
            case list() as vals:
                return vals
            case _ as val:
                return [val]

        base_index = ".".join(self._index())
        sub_index = ".".join(self._subindex())
        raise TomlAccessError(f"TomlerIterProxy Failure: {base_index}[?].{sub_index}")

    def _get_flat(self) -> Tomler | list:
        all_available = []
        for entry in self._value[0]:
            try:
                match entry() if isinstance(entry, TomlerProxy) else entry:
                    case None:
                        pass
                    case list():
                        all_available += entry
                    case dict():
                        all_available.append(entry)
                    case Tomler():
                        all_available.append(entry._table())
                    case _:
                        all_available.append(entry)
            except TomlAccessError:
                continue

        match bool(all_available), self._fallback:
            case True, _:
                pass
            case _, None:
                pass
            case _, (None,):
                return None
            case _, list():
                all_available += self._fallback
            case _, _:
                all_available.append(self._fallback)

        if bool(all_available) and all(isinstance(x, dict) for x in all_available):
            merged = Tomler.merge(*all_available)
            return merged
        if bool(all_available):
            return all_available

        base_index = ".".join(self._index())
        sub_index = ".".join(self._subindex())
        raise TomlAccessError(f"TomlerIterProxy Failure: {base_index}[?].{sub_index}")

    def _get_match(self):
        """
        Get a table from an array if it matches a set of key=value pairs
        """
        for entry in self._value[0]:
            try:
                for x in self._subindex():
                    entry = getattr(entry, x)
                if all(getattr(entry, x) == y for x,y in self._kind.items()):
                    return entry
            except TomlAccessError:
                continue

        base_index = ".".join(self._index())
        sub_index = ".".join(self._subindex())
        raise TomlAccessError(f"TomlerIterProxy Match Failure: {base_index}[?].{sub_index} != {self._match}")

    def inject(self, val=None, attr=None) -> TomlerIterProxy:
        new_index = self._index()
        if attr:
            new_index.append(attr)
        return TomlerIterProxy(val or self.value[0], types=self._types, fallback=self._fallback, index=new_index, kind=self._kind)

    def _match_type(self):
        pass

    def update_index(self, attr):
        self.__subindex.append(attr)

class ProxyEntryMixin:

    def on_fail(self, val, types=None) -> TomlerProxy:
        """
        use a fallback value in an access chain,
        eg: doot.config.on_fail("blah").this.doesnt.exist() -> "blah"

        *without* throwing a TomlAccessError
        """
        index = self._index()
        table = self._table()
        if index != ["<root>"]:
            raise TomlAccessError("On Fail not declared at entry", index)

        return Tomler(table, index, proxy=TomlerProxy(val, types=types))

    def first_of(self, fallback=None, types=None) -> TomlerIterProxy:
        """
        get the first value from a index path, even across arrays of tables
        so instead of: data.a.b.c[0].d
        just:          data.first_of().a.b.c.d()
        """
        index = self._index()[:]
        table = self._table()
        match fallback:
            case None:
                fallback = getattr(self, "__proxy")
            case TomlerProxy():
                fallback = fallback()
            case _:
                fallback = fallback

        if index != ["<root>"]:
            raise TomlAccessError("Any Of not declared at entry", index)
        proxy = TomlerIterProxy(fallback=fallback, types=types, kind="any")
        return Tomler(table, index, proxy=proxy)

    def all_of(self, fallback=None, types=None) -> TomlerIterProxy:
        index = self._index()[:]
        table = self._table()
        match fallback or getattr(self, "__proxy"):
            case None:
                proxy = TomlerIterProxy(kind="all")
            case TomlerProxy():
                proxy = TomlerIterProxy(fallback=fallback(), types=types, kind="all")
            case _:
                proxy = TomlerIterProxy(fallback=fallback, types=types, kind="all")

        if index != ["<root>"]:
            raise TomlAccessError("All Of not declared at entry", index)
        return Tomler(table, index, proxy=proxy)

    def flatten_on(self, fallback=None) -> TomlerIterProxy:
        """
        combine all dicts at the call site to form a single dict
        """
        if not isinstance(fallback, (type(None), dict)):
            raise TypeError()

        index = self._index()[:]
        table = self._table()
        match fallback or getattr(self, "__proxy"):
            case None:
                fallback = {}
            case TomlerProxy() as proxy:
                fallback = proxy()
            case _:
                pass

        if index != ["<root>"]:
            raise TomlAccessError("Flatten On not declared at entry", index)
        proxy = TomlerIterProxy(fallback=fallback, kind="flat")
        return Tomler(table, index, proxy=proxy)

    def match_on(self, **kwargs) -> TomlerIterProxy:
        index = self._table()[:]
        table = self._table()
        if index != ["<root>"]:
            raise TomlAccessError("Match On not declared at entry", index)
        proxy = TomlerIterProxy(fallback=kwargs, kind="match")
        return Tomler(table, index, proxy=proxy)

class LoaderMixin:

    @staticmethod
    def read(text:str) -> self:
        logging.debug("Reading Tomler for text")
        try:
            return Tomler(toml.loads(text))
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", text, err.args) from err

    @staticmethod
    def from_dict(data:dict) -> self:
        logging.debug("Making Tomler from dict")
        try:
            return Tomler(data)
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", data, err.args) from err

    @staticmethod
    def load(*paths:str|pl.Path) -> self:
        logging.debug("Creating Tomler for %s", paths)
        try:
            texts = []
            for path in paths:
                texts.append(pl.Path(path).read_text())

            return Tomler(toml.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("Tomler Failed to Load: ", paths, err.args) from err

    @staticmethod
    def load_dir(dirp:str|pl.Path) -> self:
        logging.debug("Creating Tomler for directory: %s", str(dirp))
        try:
            texts = []
            for path in pl.Path(dirp).glob("*.toml"):
                texts.append(path.read_text())

            return Tomler(toml.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("Tomler Failed to Directory: ", dirp, err.args) from err

class TomlerBase(dict):
    """
    Provides access to toml data (Tomler.load(apath))
    but as attributes (data.a.path.in.the.data)
    instead of key access (data['a']['path']['in']['the']['data'])

    while also providing typed, guarded access:
    data.on_fail("test", str | int).a.path.that.may.exist()

    while it can then report missing paths:
    data.report_defaulted() -> ['a.path.that.may.exist.<str|int>']
    """

    _defaulted : ClassVar[list[str]] = []

    def report_defaulted() -> list[str]:
        """
        Report the index paths inject default values
        """
        return Tomler._defaulted[:]

    def __init__(self, data:dict, index:None|list=None, proxy:TomlerIterProxy=None, mutable:bool=False):
        assert(isinstance(proxy , (NoneType, TomlerProxy))), proxy
        super_set(self, "__table", data or {})
        super_set(self, "__index"   , (index or ["<root>"])[:])
        super_set(self, "__mutable" , mutable)
        super_set(self, "__proxy"    , proxy)

    def __repr__(self):
        return f"<Tomler:{self.keys()}>"

    def __setattr__(self, attr:str, value:Any):
        if not getattr(self, "__mutable"):
            raise TypeError()
        super_set(self, attr, value)

    def __getattr__(self, attr:str) -> TomlerProxy | str | list | int | float | bool:
        table = self._table()
        proxy = super_get(self, "__proxy")

        match proxy, (table.get(attr, None) or table.get(attr.replace("_", "-"), None)):
            case None, None:
                index = self._index()
                index_s    = ".".join(index)
                available = " ".join(self.keys())
                raise TomlAccessError(f"{index_s} not found, available: [{available}]")
            case TomlerIterProxy(), [] | None:
                # logging.debug("Iter []")
                return proxy.inject(Tomler([], self._index() + [attr]), attr=attr)
            case TomlerProxy(), None:
                # logging.debug("Proxy, None")
                return proxy.inject(None, attr=attr)
            case TomlerIterProxy(), list() as result if all(isinstance(x, dict) for x in result):
                # logging.debug("Iter, [...]")
                return Tomler([Tomler(x, self._index() + [attr]) for x in result],
                              self._index() + [attr],
                              proxy.inject(attr=attr))
            case TomlerProxy(), dict() as result:
                return Tomler(result, self._index() + [attr], proxy.inject(attr=attr))
            case TomlerProxy(), _ as result:
                # logging.debug("Proxy, _")
                # Theres a fallback value, so the result needs to be wrapped so it can be called
                return proxy.inject(result, attr=attr)
            case None, dict() as result:
                # logging.debug("_, {}")
                return Tomler(result, self._index() + [attr])
            case None, list() as result if all(isinstance(x, dict) for x in result):
                # logging.debug("x, [{}]")
                index = self._index()
                return [Tomler(x, index[:]) for x in result]
            case None, _ as result:
                # logging.debug("x, Values")
                return result

    def __getitem__(self, keys):
        curr = self
        match keys:
            case tuple():
                for key in keys:
                    curr = curr.__getattr__(key)
            case str():
                curr = self.__getattr__(keys)

        return curr

    def __len__(self):
        return len(self._table())

    def __call__(self):
        table    = getattr(self, "__table")
        proxy    = getattr(self, "__proxy")

        match proxy:
            case None:
                raise TomlAccessError("Calling a Tomler only work's when guarded with a proxy")
            case TomlerIterProxy() if all(isinstance(x, dict) for x in table.values()):
                return proxy.inject(table.values())()
            case TomlerIterProxy():
                return proxy.inject([table])()
            case TomlerProxy():
                return proxy.inject(self.keys())()

    def __iter__(self):
        return iter(getattr(self, "__table").items())

    def __contains__(self, other):
        return other in self.keys()

    def _index(self):
        return super_get(self, "__index")[:]

    def _table(self):
        return super_get(self, "__table")

    def get(self, key, default=None) -> Any:
        if key in self:
            return self[key]

        return default

    def keys(self):
        # table  = object.__getattribute__(self, "__table")
        table = super_get(self, "__table")
        return list(table.keys())

    def items(self):
        # match object.__getattribute__(self, "__table"):
        match super_get(self, "__table"):
            case dict() as val:
                return val.items()
            case list() as val:
                return zip(val, val)
            case _:
                raise TypeError()

    def values(self):
        # match object.__getattribute__(self, "__table"):
        match super_get(self, "__table"):
            case dict() as val:
                return val.values()
            case list() as val:
                return val
            case _:
                raise TypeError()

    def update_index(self, attr):
        super_get(self, "__index").append(attr)
        proxy = super_get(self, "__proxy")
        if proxy:
            proxy.update_index(attr)

class Tomler(TomlerBase, ProxyEntryMixin, LoaderMixin):

    @staticmethod
    def merge(*tomlers:self, dfs:callable=None, index=None, shadow=False) -> self:
        """
        Given an ordered list of tomlers, convert them to dicts,
        update an empty dict with each,
        then wrap that combined dict in a tomler
        # TODO if given a dfs callable, use it to merge more intelligently
        """
        curr_keys = set()
        for data in tomlers:
            new_keys = set(data.keys())
            if bool(curr_keys & new_keys) and not shadow:
                raise KeyError("Key Conflict:", curr_keys & new_keys)
            curr_keys |= new_keys

        return Tomler.from_dict(ChainMap(*tomlers))
