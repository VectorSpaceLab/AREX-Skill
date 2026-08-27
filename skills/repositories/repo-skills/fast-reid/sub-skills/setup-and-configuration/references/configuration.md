# FastReID configuration lifecycle

## Scope

This reference covers the public configuration flow used by the setup and
configuration sub-skill:

1. create a fresh config
2. merge a YAML recipe
3. apply command-line overrides
4. optionally freeze the result
5. inspect selected keys

It also covers source-only import setup, `_BASE_` inheritance, and safe YAML
loading.

## Core config objects

- `fastreid.config.get_cfg()` returns a fresh cloned `CfgNode` built from the
  default config.
- `CfgNode.merge_from_file(path, allow_unsafe=False)` loads a YAML recipe and
  resolves `_BASE_` inheritance recursively.
- `CfgNode.merge_from_list([...])` applies command-line overrides as
  alternating `KEY VALUE` pairs.
- `CfgNode.freeze()` locks the config after all merges are complete.
- `CfgNode.defrost()` reopens a frozen config when later code still needs to
  mutate it.

## Source-only import setup

This repository does not ship packaging metadata, so a normal editable install
is not available. For inspection and validation, make the checkout importable by
one of these safe methods:

- add the checkout root to `PYTHONPATH`
- place a private `.pth` file in the environment's site-packages directory that
  points at the checkout root
- use a helper script that adds the checkout root to `sys.path` before import

Do not rely on distribution metadata for version checks in this repository.
Use the module version instead.

## Safe loading rules

`merge_from_file()` defaults to `allow_unsafe=False`.

- Keep the default for ordinary config inspection.
- Only opt in to unsafe loading for a trusted config that intentionally uses
  YAML tags or Python objects.
- Never use unsafe loading on untrusted input.

## Common keys to inspect or override

| Key | Default meaning | Common setup change |
| --- | --- | --- |
| `MODEL.DEVICE` | `cuda` | Set to `cpu` for dry-runs or explicit `cuda:0` for GPU use. |
| `MODEL.WEIGHTS` | empty string | Point to a checkpoint file when evaluating or resuming from weights. |
| `MODEL.BACKBONE.PRETRAIN` | `False` in defaults, often `True` in recipes | Keep `False` for shape-only smoke; enable only when you want pretrained backbone behavior. |
| `MODEL.BACKBONE.PRETRAIN_PATH` | empty string | Set a local pretrained backbone path when not using automatic downloads. |
| `DATASETS.NAMES` | `("Market1501",)` | Replace with the target benchmark family. |
| `DATASETS.TESTS` | `("Market1501",)` | Replace with the evaluation dataset family. |
| `SOLVER.IMS_PER_BATCH` | `64` | Reduce for CPU inspection or increase only when the hardware supports it. |
| `TEST.IMS_PER_BATCH` | `64` | Reduce for smaller validation memory use. |
| `INPUT.SIZE_TRAIN` / `INPUT.SIZE_TEST` | `256 x 128` | Keep the recipe default unless the selected config family intentionally changes it. |
| `OUTPUT_DIR` | `logs/` | Point to a local experiment directory if you need to preserve merged results. |

## `_BASE_` inheritance

FastReID recipes often inherit from a base file.

- The `_BASE_` path is resolved relative to the YAML file that declares it.
- Base inheritance is recursive, so a recipe may inherit from a base that itself
  inherits from another base.
- Use the merged config, not the leaf file alone, when reasoning about the final
  solver, input, head, and loss settings.
- The config merge checker in this sub-skill is the safest way to verify the
  resolved result.

### Typical inheritance patterns

- `Base-bagtricks.yml` → standard BoT-style baseline with ResNet backbones and
  BNNeck.
- `Base-AGW.yml` → AGW-style baseline with non-local and GeM settings.
- `Base-SBS.yml` → stronger baseline with CircleSoftmax, GeM-P, AMP, and longer
  crops.
- `Base-MGN.yml` → MGN-style multi-branch architecture built on top of the SBS
  family.

## Config lifecycle pattern

A safe setup flow looks like this:

1. `cfg = get_cfg()`
2. `cfg.merge_from_file(<recipe>)`
3. `cfg.merge_from_list(["MODEL.DEVICE", "cpu", ...])`
4. `cfg.freeze()` when you are done mutating
5. inspect the merged keys or hand the config to the next workflow

If you need to change the config again after freezing, call `defrost()` first.

## Command-line overrides

Use dotted keys and alternating values.

- Good: `MODEL.DEVICE cpu`
- Good: `DATASETS.NAMES Market1501`
- Good: `MODEL.WEIGHTS <CHECKPOINT_FILE.pth>`
- Bad: odd numbers of tokens
- Bad: keys that are not part of the config tree

Values are parsed by the config system, so quote strings that contain spaces.

## CPU-friendly dry-run patterns

Use these patterns when you want to confirm config behavior without training:

```bash
python scripts/config_merge_check.py \
  --repo-root <FASTREID_REPO> \
  --config-file <CONFIG_YAML> \
  --opts MODEL.DEVICE cpu
```

```bash
python scripts/config_merge_check.py \
  --repo-root <FASTREID_REPO> \
  --config-file <CONFIG_YAML> \
  --freeze \
  --show MODEL.DEVICE \
  --show MODEL.BACKBONE.NAME \
  --show DATASETS.NAMES \
  --show OUTPUT_DIR
```

If the machine is offline, pair the merged config with a local
`MODEL.WEIGHTS` or `MODEL.BACKBONE.PRETRAIN_PATH` instead of expecting a
pretrain download.
