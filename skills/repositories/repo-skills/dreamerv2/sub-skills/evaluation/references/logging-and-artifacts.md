# Logging and artifact contract

## Run outputs

Both `dreamerv2.train` and `dreamerv2.api.train` create the configured
`logdir`, save `config.yaml`, print the resolved log directory, and normally
attach three logger outputs: terminal, JSONL, and TensorBoard. The built-in
training path additionally maintains replay directories and checkpoints.

```text
<logdir>/
  config.yaml
  metrics.jsonl
  events.out.tfevents.<...>
  variables.pkl                 # after an agent save
  train_episodes/               # replay storage for built-in training
  eval_episodes/                # built-in evaluation replay storage
  crafter/                      # optional Crafter render/output subtree
```

The API path creates `train_episodes/`; the built-in path creates both
`train_episodes/` and `eval_episodes/`. `variables.pkl` is a checkpoint, not a
metric source. Never use its presence as evidence that metrics were flushed.
The training and evaluation subdirectories are replay artifacts, not plot
inputs.

For the plotting loader, organize collections as:

```text
<indir>/<task>/<method>/<seed>/metrics.jsonl
```

The plot implementation recursively discovers JSONL files, but obtains
`task`, `method`, and `seed` from the final three path components before the
file. A parent such as `<indir>/batch-01/<task>/<method>/<seed>/metrics.jsonl`
therefore changes the interpreted task to `method` and causes confusing
filtering or missing-key behavior. Move or symlink the run directories so the
input root is the task-level collection root, or use separate `--indir` roots.

## JSONL schema

`common.Logger` buffers tuples `(step, name, numpy_value)` until `write()`.
`JSONLOutput` keeps scalar values only and appends one JSON object per flush:

```json
{"step": 100000, "eval_return": 18.5, "eval_length": 1000.0, "loss": 0.42}
```

The required field is `step`; every other field is a scalar metric name and a
JSON number. A row can contain different metric keys from its neighbors. The
logger does not write images or videos to JSONL. If no metrics are buffered,
`write()` returns without creating a row. The file is append-only, so a crash
can leave an incomplete final line; the plotting loader silently ignores only
an incomplete last line, while an invalid earlier line makes that file invalid.

Built-in `train.py` names common episode metrics with `train_` or `eval_`
prefixes (`train_return`, `eval_return`, lengths, sums, means, maxima, and
replay stats), and report metrics use the same prefix. The API workflow logs
unprefixed episode `return` and `length` plus configured episode summaries and
agent metrics. Use the actual columns printed by `plot_help.py --validate-layout`
or by pandas rather than assuming `eval_return` exists.

The logger validates scalar/image/video values by rank: rank 0 is scalar, rank
2 or 3 is an image, and rank 4 is a video. Values with any other rank raise a
`ValueError`. Scalar values are converted to Python `float` before JSON
serialization. The `step` is `int(counter) * multiplier`; built-in training
sets that multiplier to `action_repeat`.

## TensorBoard events

`TensorBoardOutput` lazily creates a TensorFlow summary writer at the logdir,
flushes it after every logger call, and writes:

- scalar metrics at `scalars/<name>`;
- rank-2 and rank-3 values as images;
- rank-4 values as GIF-backed summaries using the configured FPS.

Use the same root passed as `logdir`:

```sh
tensorboard --logdir /absolute/path/to/logs
```

Event files are binary and may exist even when `metrics.jsonl` is absent or
empty, depending on which output was configured and whether a flush occurred.
Conversely, a custom `outputs=[JSONLOutput(...)]` API run can have JSONL
without TensorBoard events. Inspect each output independently.

For video summaries, floating arrays are clipped from `[0, 1]` into `uint8`
`[0, 255]`. The GIF encoder invokes `ffmpeg` from `PATH` and supports one or
three channels. If `ffmpeg` is missing or exits unsuccessfully, the logger
prints `GIF summaries require ffmpeg in $PATH.` and falls back to a TensorFlow
image summary for that value. Thus missing ffmpeg can remove animated GIF
summaries but does not by itself prevent scalar logging or scalar TensorBoard
curves. A malformed video shape/channel count can fail before or during the
fallback and should be treated separately from a missing executable.

## Reading data safely

```python
from pathlib import Path
import pandas as pd

path = Path("/absolute/path/to/metrics.jsonl")
if not path.is_file() or not path.stat().st_size:
    raise SystemExit(f"No non-empty metrics file: {path}")
frame = pd.read_json(path, lines=True)
required = {"step", "eval_return"}
missing = required - set(frame.columns)
if missing:
    raise SystemExit(f"Missing columns: {sorted(missing)}")
frame = frame.dropna(subset=sorted(required)).sort_values("step")
print(frame.tail())
```

Use `--validate-layout` in the bundled helper when pandas is unavailable; it
checks file placement and JSON lines with only the Python standard library.
Use pandas for numerical filtering or plotting because the source plot module
imports both pandas and matplotlib at startup.
