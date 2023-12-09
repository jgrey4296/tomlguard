# TomlGuard
Author: John Grey
Date  : 2022-12-06

## Overview

A Python Toml wrapper to make things a bit less annoying.


## Examples

With some toml:

``` toml
[person]
name    = "bob"
age     = 26
friends = ["bill", "jill", "jim"]

```



``` python
import pathlib as pl
import tomlguard as TG

data = TG.load("basic.toml")
# Or load all tomls concatenated together:
# data = TG.load_dir(pl.Path())

print(data.person.name)    # -> bob
print(data.person.age)     # -> 26
print(data.person.friends) # -> ["bill", "jill", "jim"]

print(data.on_fail("Fallback", str).this.doesnt.exist()) # -> "Fallback"
print(data.on_fail("bill?").person.name()) # -> bob

try:
    print(data.on_fail("a string", str).person.age())
except TypeError:
    print("Type Mismatch")

print(TG.TomlGuard.report_defaulted()) # -> ['this.doesnt.exist = "Fallback" # <str>']

# TODO: explain all_of, any_of, match_on for multi-tables
```
