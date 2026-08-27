# Configuration API reference

This reference describes the public behavior implemented by gradSLAM's
`gradslam.config.CfgNode`.

## Construction and access

```python
from gradslam.config import CfgNode

cfg = CfgNode({
    "MODEL": {"NAME": "tiny"},
    "TRAIN": {"LR": 0.1, "SCALES": (1, 2)},
})
cfg.MODEL.NAME
cfg["TRAIN"]["LR"]
```

`CfgNode(init_dict=None, key_list=None, new_allowed=False)` deep-copies the
initial mapping. Nested dictionaries become nested `CfgNode` objects. Valid
leaf types are exactly `tuple`, `list`, `str`, `int`, `float`, and `bool`.
`None`, arbitrary objects, and other leaf types are rejected. `key_list` is an
internal path context used in validation messages; callers normally leave it
unset.

Attribute assignment validates the value and rejects writes while the node is
frozen. Assigning a plain dictionary as an attribute is not a supported leaf
assignment; wrap it in `CfgNode` first. Missing attribute lookup raises
`AttributeError`, rather than creating a key.

## Serialization and loading

- `cfg.dump(**kwargs)` recursively converts nodes to dictionaries and calls
  `yaml.safe_dump`; keyword arguments are passed to the YAML dumper.
- `str(cfg)` prints keys sorted at each level with a compact, indented tree.
  Tuple values retain Python tuple notation in this view.
- `repr(cfg)` identifies the class and uses dictionary-style representation,
  such as `CfgNode({'A': 1})`. It is for diagnostics, not a loading contract.
- `CfgNode.load_cfg(value)` (also available as `load_cfg`) accepts a YAML
  string or an `io.IOBase` file object. A file object is selected by its
  filename extension: no extension, `.yml`, and `.yaml` are YAML; `.py` is a
  Python source file.
- A Python source file must export `cfg`, whose exact type is `dict` or
  `CfgNode`. The exported value is copied into a new node.
- `merge_from_file(path)` opens a path, loads it according to its extension,
  and merges it into the receiver. A path passed directly to `load_cfg` is not
  treated as a filename; a string argument is parsed as YAML text.

YAML is parsed with `yaml.safe_load`. A YAML `null` leaf therefore does not
satisfy the allowed leaf-type contract. A temporary file used with
`load_cfg(file_obj)` must have an appropriate `.name` suffix when the caller
wants Python loading rather than YAML loading.

## Merge methods

`merge_from_other_cfg(cfg_other)` recursively overlays a `CfgNode`. Existing
keys are replaced, and nested nodes are merged. The receiver's schema controls
whether unknown keys are accepted. `merge_from_file(path)` is the file-loading
front end for the same operation.

`merge_from_list(cfg_list)` expects an even-length sequence:

```python
cfg.merge_from_list([
    "TRAIN.LR", "0.02",
    "MODEL.NAME", "'tiny-v2'",
])
```

Each value is decoded with `ast.literal_eval` when possible. Thus `"0.02"`
becomes a float, `"(4, 8)"` becomes a tuple, `"[4, 8]"` becomes a list, and
an unquoted token such as `tiny-v2` remains a string. The path and final key
must already exist for list overrides; `new_allowed` does not create a missing
CLI path. List pairs are processed in order, so a later pair wins.

## Type checks and coercion

When an overlay replaces an existing value, the type must match exactly except
for the two supported conversions:

- list to tuple, when the original is a tuple;
- tuple to list, when the original is a list.

A scalar-to-string, integer-to-float, or boolean-to-integer replacement raises
`ValueError`. A nested incoming dictionary is decoded to a `CfgNode` before
recursive merging. New values admitted by `new_allowed` still need a valid
leaf type or nested configuration node.

## New-key boundaries

`CfgNode(new_allowed=True)` changes only that node's merge boundary. For
example, if `cfg.EXTRA` permits new keys, `EXTRA.NEW` may be added by a tree or
file merge. A pre-existing child such as `EXTRA.NESTED` keeps its own
`new_allowed` setting; if it was constructed with the default `False`, an
unknown key below it is rejected. Do not infer permissiveness from an ancestor.

## Mutability and copies

- `freeze()` recursively marks this node and every nested node immutable.
- `defrost()` recursively marks this node and every nested node mutable.
- `is_frozen()` reports the receiver's state.
- `clone()` returns a recursive `copy.deepcopy` copy, including nested values
  and configuration metadata.

Use `clone()`, `defrost()`, edit, and `freeze()` for safe variants. The
attribute guard is implemented in `__setattr__`; merge methods write through
the dictionary interface, so callers should not use a merge as a substitute
for an explicit frozen-state policy.

## Legacy-key diagnostics

`register_deprecated_key("OLD.KEY")` records an ignored key. A matching key in
a list or an unknown key in a tree/file merge is skipped and logs a warning.
`register_renamed_key(old_name, new_name, message=None)` records a key that
must be migrated. A matching merge raises `KeyError`; when `message` is
provided it is appended as migration guidance. Registration is exact and uses
the full dotted key.

`key_is_deprecated`, `key_is_renamed`, `raise_key_rename_error`, and
`is_new_allowed` expose the corresponding checks. They do not normalize case
or partial paths.
