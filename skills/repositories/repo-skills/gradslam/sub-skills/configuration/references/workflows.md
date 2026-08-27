# Configuration workflows

## 1. Define a strict base schema

Start with all keys that downstream code is allowed to consume. Construct
nested dictionaries directly when their initial values are known:

```python
from gradslam.config import CfgNode as CN

cfg = CN({
    "MODEL": {"NAME": "tiny", "LAYERS": (1, 2)},
    "TRAIN": {"LR": 0.1},
})
```

For a deliberately extensible section, create that node explicitly:

```python
cfg.EXTRA = CN(new_allowed=True)
cfg.EXTRA.SEED = 7
cfg.EXTRA.NESTED = CN()  # remains strict at this child boundary
```

Use `cfg.MODEL.NAME` for known fields. Use `cfg[dynamic_name]` only when the
key is supplied dynamically and has already been validated.

## 2. Load and layer configuration sources

A typical precedence order is base schema, file/tree overlay, then CLI-style
pairs:

```python
cfg.merge_from_file("experiment.yaml")
cfg.merge_from_other_cfg(CN({"TRAIN": {"LR": 0.05}}))
cfg.merge_from_list(["TRAIN.LR", "0.01", "MODEL.NAME", "'tiny-cli'"])
```

Each operation mutates the receiver. Later operations override values changed
by earlier operations. Tree/file merges recurse into existing nodes; they do
not replace the whole root with an unvalidated dictionary.

For an in-memory YAML document, use `CN.load_cfg(yaml_text)` and merge the
returned node. For a Python config file, use `merge_from_file` or open the file
as an `io.IOBase` and call `CN.load_cfg`; its `cfg` export must be a `dict` or
`CfgNode`. Do not pass a filesystem path to `CN.load_cfg` expecting path
loading: a string is YAML text.

## 3. Make CLI overrides predictable

Represent command-line options as alternating key/value items. Keep all pairs
in one list and ensure the length is even:

```python
opts = [
    "TRAIN.LR", "0.02",
    "MODEL.LAYERS", "[3, 4]",
    "MODEL.NAME", "tiny-cli",
]
cfg.merge_from_list(opts)
```

The `MODEL.LAYERS` value is decoded as a list, then coerced to the original
tuple. The unquoted `tiny-cli` token remains a string because it is not a
Python literal. Quote strings that look like numbers, booleans, lists, or
`None` when those spellings must remain text. If a value contains shell
metacharacters, let the caller's argument parser deliver one intact list item;
this skill does not parse a shell command line.

A list override requires every path component and final key to exist. To add a
new field, use a tree/file merge into a node whose local `new_allowed` is true;
do not expect a list override to bypass the schema.

## 4. Use new-key boundaries intentionally

Permit additions only in a named extension section:

```python
cfg.EXTRA = CN(new_allowed=True)
cfg.EXTRA.BASE = 1
cfg.merge_from_other_cfg(CN({"EXTRA": {"PLUGIN": {"ENABLED": True}}}))
```

The complete new `PLUGIN` subtree is admitted at `EXTRA`. If `PLUGIN` already
exists as a strict node, a new field below it is rejected. This makes the
boundary local rather than recursively permissive. Test both sides of the
boundary before accepting user-supplied overlays.

## 5. Freeze and create a variant

Freeze only after all intended merges and validation:

```python
cfg.freeze()
assert cfg.is_frozen() and cfg.MODEL.is_frozen()

variant = cfg.clone()
variant.defrost()
variant.MODEL.NAME = "tiny-ablation"
variant.freeze()
```

Direct attribute writes to a frozen node raise `AttributeError`. A clone is
independent, and `defrost()` applies recursively. The implementation's merge
methods assign mapping entries directly; therefore the safe operational rule
is to merge before freezing, or explicitly defrost a clone before merging.

## 6. Migrate legacy configuration keys

Register exact full paths at the root before applying overlays:

```python
cfg.register_deprecated_key("TRAIN.OLD_SCHEDULE")
cfg.register_renamed_key(
    "MODEL.OLD_NAME", "MODEL.NAME", message="Use the new string field."
)
```

Deprecated keys are ignored with a warning. Renamed keys raise `KeyError` and
include the replacement (and optional message). Treat the exception as a
migration prompt rather than silently rewriting the input. Registration does
not create either key in the tree.

## 7. Inspect and persist

Use `cfg.dump()` when a YAML representation is needed, optionally passing safe
YAML dumper keyword arguments. Use `str(cfg)` for a stable, readable tree and
`repr(cfg)` when diagnosing the node type. A dump may serialize tuples using a
YAML sequence; merging that dump back into a schema with a tuple value applies
the supported list-to-tuple coercion.
