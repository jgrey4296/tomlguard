# TomlGuard Architecture Notes

The publicly usable class of TomlGuard is `tomlguard.tomlguard:TomlGuard`.
This just subclasses `tomlguard.base:GuardBase` and mixs in

`tomlguard.base:GuardBase` as the core class, handles the main functionality of
mapping `str` keys to `TomlType`s (`int`, `float`, `list`, `dict`, `bool` etc),
providing the attribute and index access capabilities.

Mixins add particular extra capabilities:

## `tomlguard.utils.proxy_mixin:ProxyEntryMixin`
This adds the methods `on_fail`, `first_of`, `all_of`, `flatten_on`, and `match_on`,
to give limited ways of delayed reading and error handling.
`toml.utils.proxy`

## `tomlguard.utils.iter_proxy`

## `tomlguard.utils.writing`

## `tomlguard.utils.loader`
