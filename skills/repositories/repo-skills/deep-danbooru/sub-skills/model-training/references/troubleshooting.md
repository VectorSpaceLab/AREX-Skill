# Training troubleshooting

## Fast diagnosis table

| Symptom | Likely cause | Action |
|---|---|---|
| `Not supported model` | `model` is not an exact dispatch string. | Use only `resnet_152`, `resnet_custom_v1`, `resnet_custom_v2`, `resnet_custom_v3`, or `resnet_custom_v4`. |
| `Not supported optimizer` | `optimizer` is unsupported or has wrong case. | Use exactly `adam`, `sgd`, or `rmsprop`. |
| `Loss type ... is not supported` | `loss` is unsupported. | Use exactly `binary_crossentropy` or `focal_loss`. |
| Database does not exist | `database_path` is null, stale, or relative to an unexpected CWD. | Run config validation with the same `--runtime-cwd` intended for training; prefer an absolute dataset path. |
| `no such table: posts` / missing column | Wrong file or malformed schema. | Return to [project-data-setup](../../project-data-setup/SKILL.md) and validate the training schema. |
| Eligible row count is zero | Empty table, threshold too high, or extensions not lowercase/supported. | Inspect counts; fix data or deliberately change `minimum_tag_count`. Never lower it blindly. |
| Missing derived image paths | Database/image tree mismatch. | Place each file at `images/MD5[:2]/MD5.FILE_EXT` beside the SQLite file, or repair the row. |
| Epochs complete with implausibly few samples | `ignore_errors()` dropped image read/decode failures. | Compare selected rows with `used_sample`, scan all image paths, and run a decode smoke on each actual format. |
| Run appears stuck before offset advances | `checkpoint_frequency_mb` is zero or a slice is too expensive. | Set a positive frequency; estimate `minibatch_size * checkpoint_frequency_mb` and reduce it deliberately. |
| Logging crashes | `console_logging_frequency_mb` is zero. | Set a positive integer. |
| Restore reports shape/variable errors | Checkpoint structure no longer matches model, tags, shape, optimizer, or precision. | Restore the original project inputs or start a clean checkpoint lineage. |
| `--source-model` seems ignored | A latest project checkpoint restored after source-model loading. | Move/preserve old checkpoints and use a new empty checkpoint directory for initialization. |
| Mixed-precision export fails with an unbound float32 model | `--source-model` was combined with `mixed_precision: true`. | Use float32 source-model training or start mixed-precision construction without `--source-model`. |
| Float32 mixed export fails/restores partially | Reconstructed variables do not align with checkpoint state. | Keep the regular export/checkpoint, disable mixed precision for recovery, and validate artifacts independently. |
| TensorFlow I/O import fails | `tensorflow_io` is absent/incompatible. | Install a compatible TensorFlow I/O distribution in the chosen environment and rerun import probes. |
| No GPU is listed | CPU-only runtime or missing GPU stack. | Continue on the required verified CPU backend, or separately provision and verify a GPU environment. |

## Missing images and decode failures

The SQLite loader does not stat image files. The TensorFlow pipeline reads them
later and places `ignore_errors()` after its image-loading map. Missing,
zero-byte, corrupt, or unsupported payloads may therefore be removed instead of
raising a terminal training error.

Run:

```console
python scripts/training_preflight.py PROJECT --max-image-checks 0
```

A complete scan can be expensive on a large filesystem, so approve its I/O
budget first. The helper checks paths, sizes, and basic PNG/JPEG signatures but
cannot prove TensorFlow decoder behavior. Use `--probe-imports
--probe-tensorflow` for runtime imports, then authorize a small decode/batch
smoke in the actual environment before full training.

The SQL selector recognizes lowercase `png`, `jpg`, and `jpeg`, while image
loading first requests PNG decoding and contains a TensorFlow-I/O WebP fallback.
Selection is not proof of successful decode. If JPEG rows disappear, reproduce
with one known JPEG and use a corrected/preconverted dataset rather than
assuming the record count reached the model.

## Empty records and empty updates

Distinguish these cases:

- **No project tags:** output dimension is zero and the run is invalid.
- **Empty `posts`:** there is no training data.
- **No eligible rows:** threshold/extension filtering removed all rows.
- **Empty/null `tag_string`:** the target is all-zero or the transform fails.
- **No usable decoded images:** records exist, but `ignore_errors()` drops all
  inputs.
- **No remaining epochs:** a restored `used_epoch` is already at or above the
  configured `epoch_count`, so only final export occurs.

A created `.keras` file is not evidence that gradient updates occurred. Inspect
`used_sample`, logs, eligible counts, and a real post-training inference case.
Do not try to fix empty data by changing the model or loss.

## Unsupported or malformed project values

The runtime raises direct exceptions for unsupported model/optimizer/loss
strings, but other malformed values fail later and less clearly. Use
`validate_project_config.py` to catch missing fields, booleans used as integers,
non-positive dimensions/batch/epoch counts, zero checkpoint/logging intervals,
bad augmentation ranges, malformed schedules, and a null database path.

`export_model_per_epoch: 0` is valid and means every epoch. Negative values are
invalid. Null or empty augmentation ranges disable that transform; non-empty
ranges need two ordered numeric endpoints, with positive scale endpoints.

## Checkpoint lineage surprises

Resume has no CLI disable flag. If `checkpoints/` contains a latest checkpoint,
training restores model, optimizer, counters, offset, and seed. Before changing
lineage:

1. stop the current process cleanly;
2. copy or rename the checkpoint directory rather than deleting it;
3. retain the matching project JSON and tag order;
4. create a new empty checkpoint location for a deliberate fresh run;
5. preflight again and record whether resume is expected.

If the restored epoch already meets `epoch_count`, the training loops are
skipped and the final model is saved. Increase the target only when continuing
the same compatible lineage.

## Learning rate and metric interpretation

A schedule is processed in list order; unsorted or duplicate `used_epoch`
entries can make the last matching entry win unexpectedly. Sort and deduplicate
the schedule. With mixed precision, the optimizer is loss-scaled but the code
still assigns through `optimizer.learning_rate`; verify the printed value at
each epoch.

Console precision and recall are Keras batch metrics. The printed F1 is derived
from the current returned precision/recall, while average loss and speed are
aggregated between logging points. These values are training telemetry, not a
held-out evaluation. Route saved-model quality checks to
[inference-evaluation](../../inference-evaluation/SKILL.md).

## Backend boundary

CPU TensorFlow is required and verified for this skill. `--probe-tensorflow`
requires at least one visible CPU. It reports visible GPUs but does not validate
CUDA libraries, kernels, memory behavior, mixed precision, or end-to-end GPU
training. Treat GPU as optional and unverified until a separate backend-specific
plan succeeds.
