# CLI Reference

## Purpose

Read this when you need the exact `train.py` and `test.py` flags, config-file selection rules, or output directory layout.

## `train.py`

```text
python train.py <cfg_file> [--iter START_ITER] [--threads THREADS]
```

| Argument | Meaning |
| --- | --- |
| `cfg_file` | Config basename without `.json`. The script loads `config/<cfg_file>.json`. |
| `--iter START_ITER` | Resume training from the specified iteration. The script loads the checkpoint for that iteration and scales the learning rate by the configured decay schedule. |
| `--threads THREADS` | Number of dataset prefetch worker processes. Defaults to `4`. |

### Behavior

- The command sets `system_configs.snapshot_name` to `cfg_file`.
- The config selects `dataset`, `batch_size`, `prefetch_size`, `train_split`, `val_split`, and optimizer settings.
- Checkpoints are saved at the configured `snapshot` interval.
- Validation runs only when `val_iter` is non-zero.

## `test.py`

```text
python test.py <cfg_file> [--testiter TESTITER] [--split SPLIT] [--suffix SUFFIX] [--debug]
```

| Argument | Meaning |
| --- | --- |
| `cfg_file` | Config basename without `.json`. The script loads `config/<cfg_file>.json` unless `--suffix` is set. |
| `--testiter TESTITER` | Checkpoint iteration to load. If omitted, the script uses the config's `max_iter`. |
| `--split SPLIT` | One of `training`, `validation`, or `testing`. These map to `trainval`, `minival`, and `testdev`. |
| `--suffix SUFFIX` | Appends `-<suffix>` to the config filename, such as `config/CenterNet-52-multi_scale.json`. |
| `--debug` | Limits the number of evaluated images and writes visualization files under `debug/`. |

### Behavior

- The command sets `system_configs.snapshot_name` to `cfg_file`.
- It loads the checkpoint before any decoding or evaluation starts.
- It writes COCO-format detections to `results.json`.
- `--suffix multi_scale` is the shipped multi-scale evaluation variant.

## Output path rules

- Training checkpoints: `cache/nnet/<snapshot_name>/<snapshot_name>_<iter>.pkl`
- Test results: `results/<snapshot_name>/<testiter>/<split>/results.json`
- Multi-scale results: `results/<snapshot_name>/<testiter>/<split>/<suffix>/results.json`
- Debug visualizations: `results/<snapshot_name>/<testiter>/<split>[/<suffix>]/debug/`

## Practical reminders

- Both CLIs import the compiled extensions at module import time.
- Both CLIs expect CUDA-capable PyTorch because the network code calls `.cuda()`.
- `train.py --help` and `test.py --help` are useful smoke checks after the environment is prepared.
