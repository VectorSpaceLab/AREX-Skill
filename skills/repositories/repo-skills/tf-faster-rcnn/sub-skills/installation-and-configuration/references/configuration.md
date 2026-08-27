# Configuration Reference

## Purpose

Read this when you need to understand `lib/model/config.py`, choose a preset from `experiments/cfgs/*.yml`, or debug a config override failure.

## Verified defaults from `lib/model/config.py`

| Setting | Default |
| --- | --- |
| `cfg.USE_GPU_NMS` | `True` |
| `cfg.TEST.MODE` | `nms` |
| `cfg.POOLING_MODE` | `crop` |
| `cfg.ANCHOR_SCALES` | `[8, 16, 32]` |
| `cfg.ANCHOR_RATIOS` | `[0.5, 1, 2]` |
| `cfg.TRAIN.SCALES` | `[600]` |
| `cfg.TEST.SCALES` | `[600]` |
| `cfg.TRAIN.SNAPSHOT_PREFIX` | network-specific |

The pure-Python smoke path also verified:

- `generate_anchors()` returns `(9, 4)` with the default anchor scales and ratios.
- `py_cpu_nms` on the tiny synthetic overlap fixture keeps indices `[0, 2]`.

## Preset catalog

| File | Main effect |
| --- | --- |
| `experiments/cfgs/vgg16.yml` | `EXP_DIR=vgg16`, `TRAIN.SNAPSHOT_PREFIX=vgg16_faster_rcnn`, `DOUBLE_BIAS=True` |
| `experiments/cfgs/res50.yml` | `EXP_DIR=res50`, `TRAIN.SNAPSHOT_PREFIX=res50_faster_rcnn` |
| `experiments/cfgs/res101.yml` | `EXP_DIR=res101`, `TRAIN.SNAPSHOT_PREFIX=res101_faster_rcnn` |
| `experiments/cfgs/mobile.yml` | `EXP_DIR=mobile`, `TRAIN.SNAPSHOT_PREFIX=mobile_faster_rcnn`, `DOUBLE_BIAS=False` |
| `experiments/cfgs/res101-lg.yml` | `EXP_DIR=res101-lg`, `TRAIN.SCALES=[800]`, `TEST.SCALES=[800]`, `TEST.RPN_POST_NMS_TOP_N=1000`, `ANCHOR_SCALES=[2,4,8,16,32]` |

## How config loading works

### `cfg_from_file`

- Loads a YAML preset and merges it into the defaults.
- Unknown keys fail fast.
- Type mismatches fail fast.
- Modern PyYAML emits a `YAMLLoadWarning` because the legacy code still calls `yaml.load()` without a loader. That warning is cosmetic for the current inspection path.

### `cfg_from_list`

This is the strict command-line override path used by the training and testing launchers.

Rules:

- The argument list must contain key/value pairs.
- Keys use dotted names like `TRAIN.SCALES` or `USE_GPU_NMS`.
- Values are parsed with Python literal semantics.
- The parsed value must have the exact same Python type as the existing config field.

Good examples:

```python
['USE_GPU_NMS', 'False']
['TRAIN.SCALES', '[800]']
['TEST.MODE', "'top'"]
['ANCHOR_SCALES', '[2,4,8,16,32]']
```

Common errors:

- `AssertionError` when the override list has an odd number of entries.
- `AssertionError` or `KeyError` when the key name is misspelled.
- `AssertionError: type <class 'int'> does not match original type <class 'list'>` when a scalar is used where a list is expected.
- `AssertionError` when `False` is passed as `0` or another non-bool literal.

## NMS mode selection

- `cfg.TEST.MODE` defaults to `nms`.
- `top` is the slower alternative and is meant for proposal selection experiments.
- `cfg.USE_GPU_NMS` only controls runtime dispatch once the compiled NMS modules exist.
- The flag does **not** make `model.nms_wrapper` importable if `nms.gpu_nms` was never built.

## Output paths driven by config

These helpers matter when later routes need a location to write artifacts:

- `get_output_dir(imdb, weights_filename)` -> `output/<EXP_DIR>/<imdb>/<weights>`
- `get_output_tb_dir(imdb, weights_filename)` -> `tensorboard/<EXP_DIR>/<imdb>/<weights>`

## When to change a preset vs. using overrides

Use a preset file when you want a durable repo-wide default, especially for a network family or a special scale/anchor schedule like `res101-lg.yml`.

Use `cfg_from_list` when you only need an invocation-specific change and the value type matches exactly.

If the override is complex or type-sensitive, edit the YAML preset or the default in `config.py` instead of forcing a mismatched command-line literal.
