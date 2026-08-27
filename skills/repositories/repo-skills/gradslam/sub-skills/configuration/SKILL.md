---
name: configuration
description: "It constructs, loads, merges, validates, and safely edits gradSLAM
  CfgNode configuration trees."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# gradSLAM configuration

Use this sub-skill when a task needs the repository's `CfgNode` rather than a
plain dictionary. `CfgNode` is a dictionary-backed tree with attribute access,
YAML/Python loading, controlled merges, type checks, mutability controls, and
legacy-key diagnostics.

## Entry points

- Import `CfgNode` from `gradslam.config` (the package also exposes the
  compatibility-level `load_cfg` alias).
- Construct from a nested dictionary, or construct an empty node and assign
  nested `CfgNode` objects.
- Read the exact method signatures and accepted file forms in
  [the API reference](references/api-reference.md).
- Follow the operation sequences in [the workflows](references/workflows.md).
- Use [the troubleshooting guide](references/troubleshooting.md) when a merge,
  type, load, or mutability operation fails.
- Run `scripts/config_smoke.py --help` before using the bundled deterministic
  check; it creates only temporary local files.

## Core operating rules

1. Keep a stable base schema in a `CfgNode`. Nested dictionaries passed to the
   constructor are recursively converted to nodes.
2. Use attribute access for known keys (`cfg.TRAIN.LR`) and dictionary access
   when a key is dynamic. Missing attributes raise `AttributeError`.
3. Apply overlays deliberately. `merge_from_file`,
   `merge_from_other_cfg`, and `merge_from_list` overwrite existing values;
   later operations win when applied sequentially.
4. Treat a list override as pairs of `FULL.KEY`, `VALUE`. Values are decoded
   with Python literal syntax where possible, so quote strings that could be
   mistaken for another literal.
5. Expect strict schema checks by default. An unknown key raises an error,
   except at a node constructed with `new_allowed=True` when merging a config
   tree or file. This setting is local to that node.
6. Existing list/tuple values may be replaced by the other container type and
   are coerced to the original type. Other replacement types must match
   exactly; do not rely on numeric or boolean coercion.
7. Freeze before handing a configuration to code that must not mutate it.
   `freeze()` propagates to nested nodes; `defrost()` propagates back. Clone
   before making an experimental variant so the base remains independent.
8. Register removed keys as deprecated when old inputs should be ignored with
   a warning. Register renamed keys when old inputs must fail with a
   replacement and optional migration message.

## Safe merge sequence

- Build or load the base schema.
- Validate that every file/list override uses an existing path unless the
  destination merge node explicitly permits new keys.
- Apply broad file/tree overlays first, then narrow CLI-style overrides.
- Inspect `cfg.dump()` for a YAML serialization and use `str(cfg)` for the
  sorted human-readable tree. `repr(cfg)` is a diagnostic representation, not
  a portable config file.
- Freeze only after all intended merges. If a variant is needed, clone it,
  defrost the clone, change it, and freeze it again.

## Diagnostics contract

- Missing attribute: `AttributeError`.
- Invalid leaf or assigned value: `AssertionError` with a key/type message.
- Unknown merge key: `KeyError`.
- Wrong replacement type: `ValueError`.
- Renamed key: `KeyError` naming the replacement and optional message.
- Deprecated key: merge is skipped and a warning is logged.
- Odd-length override list or a missing path component: `AssertionError`.

Do not treat `new_allowed=True` as recursive global permissiveness, and do not
assume `freeze()` makes every mapping-level merge method transactional. The
implementation guards attribute assignment; perform merges before freezing, or
use an explicit defrost/clone/re-freeze sequence.

## Boundaries

This sub-skill covers configuration tree mechanics only. It does not define
model, dataset, odometry, device, or command-line parser schemas. Those callers
must provide the base keys and convert their own application arguments into
`merge_from_list` pairs.
