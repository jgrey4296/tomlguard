# Tomler Architecture Notes

The publicly usable class of Tomler is `tomler.tomler:Tomler`.
This just subclasses `tomler.base:TomlerBase` and mixs in

`tomler.base:TomlerBase` as the core class, handles the main functionality of
mapping `str` keys to `TomlType`s (`int`, `float`, `list`, `dict`, `bool` etc),
providing the attribute and index access capabilities.

Mixins add particular extra capabilities:

## `toml.utils.proxy_mixin:ProxyEntryMixin`
This adds the methods `on_fail`, `first_of`, `all_of`, `flatten_on`, and `match_on`,
to give limited ways of delayed reading and error handling.
`toml.utils.proxy`

## `toml.utils.iter_proxy`

## `toml.utils.writing`

## `toml.utils.loader`
