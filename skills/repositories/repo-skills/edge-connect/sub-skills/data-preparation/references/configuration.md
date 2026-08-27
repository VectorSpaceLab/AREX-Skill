# Configuration guidance

This reference covers the EdgeConnect config keys that matter for data preparation, path validation, and mode-dependent input behavior.

## Runtime config behavior
- The loader reads `config.yml` from the checkpoint directory.
- If that file does not exist, the template is copied in first.
- `PATH` is assigned at runtime from the config file directory and should not be set manually in YAML.
- Missing keys fall back to defaults from the config loader.
- Explicit `0` values are preserved; only missing or `null` values fall back.

## Path resolution rule
EdgeConnect uses the path strings exactly as stored in the config or CLI arguments. Relative dataset paths are resolved from the current working directory at runtime, not from the config file directory.

## Data-related keys

| Key | Meaning | Notes |
| --- | --- | --- |
| `TRAIN_FLIST` | Training image list, directory, or single file path | Required for training and eval initialization |
| `VAL_FLIST` | Validation image list, directory, or single file path | Required for training and eval initialization; also used for validation and sampling |
| `TEST_FLIST` | Test image list, directory, or single file path | Required for test mode |
| `TRAIN_EDGE_FLIST` | Training external edge list | Required only when `EDGE=2` |
| `VAL_EDGE_FLIST` | Validation external edge list | Required only when `EDGE=2` and validation is used |
| `TEST_EDGE_FLIST` | Test external edge list | Required only when `EDGE=2` in test mode |
| `TRAIN_MASK_FLIST` | Training external mask list | Required when `MASK=3`, `4`, or `5` |
| `VAL_MASK_FLIST` | Validation external mask list | Required when `MASK=3`, `4`, or `5` and validation is used |
| `TEST_MASK_FLIST` | Test external mask list | Required in test mode because `MASK` becomes `6` |
| `RESULTS` | Optional output directory override | Used for test outputs |

## Mode keys
| Key | Values | Why it matters for data prep |
| --- | --- | --- |
| `MODE` | `1` train, `2` test, `3` eval | Selects which flists are consumed |
| `MODEL` | `1` edge, `2` inpaint, `3` edge-inpaint, `4` joint | Affects whether edge lists are actually used |
| `MASK` | `1` random block, `2` half, `3` external, `4` external + random block, `5` external + random block + half | Decides whether mask flists are needed |
| `EDGE` | `1` Canny, `2` external | Decides whether edge flists are needed |
| `NMS` | `0` off, `1` on | Only affects external edge maps |
| `SIGMA` | Canny blur strength, `0` random, `-1` none | Relevant only when `EDGE=1` |

## Fallback behavior
The loader consults defaults when a key is missing or set to `null`.

### Important defaults
- `MODE` defaults to train.
- `MASK` defaults to external masks.
- `EDGE` defaults to Canny.
- `NMS` defaults to on.
- `INPUT_SIZE` defaults to `256`.

### Practical effect
If you omit `MASK` from YAML, the model behaves as if `MASK=3`, which means external masks are expected.
If you omit `EDGE`, the model behaves as if `EDGE=1`, which means no edge flist is required.

## Mode-specific path requirements
- Train mode and eval mode both initialize train and validation datasets, so they require `TRAIN_FLIST` and `VAL_FLIST`.
- Test mode uses only the test dataset, so it requires `TEST_FLIST` and `TEST_MASK_FLIST`.
- External edge lists are required wherever `EDGE=2` is active for the selected mode.
- External mask lists are required wherever `MASK=3`, `MASK=4`, or `MASK=5` is active for the selected mode.

## Test-mode override
When running in test mode, the loader forces:
- `INPUT_SIZE=0`
- `MASK=6`
- the test flists supplied by the current config or CLI

That means test masks must be index-aligned with test images.
