---
name: evaluation
description: "Evaluate DreamerV2 runs from JSONL and TensorBoard artifacts,
  compare seeds and baselines, and diagnose plotting failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DreamerV2 evaluation

Use this skill after a run has produced a log directory. It covers artifact
inspection, scalar loading, TensorBoard viewing, and the package plotting CLI.
It does **not** launch training, construct environments, or build the Python
runtime; route those requests to the sibling training, environments, and
configuration skills.

## Fast route

1. Identify the run root and check that each run is exactly
   `task/method/seed/metrics.jsonl` below an input directory. Do not hide an
   extra experiment-name directory from the plot loader.
2. Run the dependency-free [plot helper](scripts/plot_help.py) from any working
   directory:

   ```sh
   python /path/to/evaluation/scripts/plot_help.py --validate-layout \
     --indir "$LOG_ROOT"
   ```

   Add `--xaxis step --yaxis eval_return` when checking a particular metric.
3. Open scalar data directly with pandas or inspect TensorBoard. The complete
   artifact contract is in [logging and artifacts](references/logging-and-artifacts.md).
4. Plot only after the layout and metric names are present. The plotting
   details, exact flags, binnings, aggregation, and baseline discovery rules
   are in [plotting](references/plotting.md).

The helper is a checker and installed-package adapter, not a copy of the
long renderer. Ask the adapter for the installed renderer's help, or forward
plot flags with `--render`:

```sh
python /path/to/evaluation/scripts/plot_help.py --renderer-help
python /path/to/evaluation/scripts/plot_help.py --render \
  --indir "$LOG_ROOT" --outdir "$PLOT_ROOT" \
  --xaxis step --yaxis eval_return --bins 1e6
```

The legacy `dreamerv2.common.plot` source imports a top-level `common` alias,
so a bare `python -m dreamerv2.common.plot` is not portable in an installed
package. The bundled adapter resolves the installed package directory and
runs its `common/plot.py` without a checkout path.

`--indir` and `--outdir` are required by the renderer. `--subdir True` (the
default) appends the first input directory's basename to `--outdir`; use
`--subdir False` when the output path must be exact. The known broken installed
console launcher is not the plotting route; use a module invocation for
training as well (`python -m dreamerv2.train`) rather than `dreamerv2`.

## What to inspect

A normal built-in run looks like this:

```text
LOG_ROOT/
  atari_pong/
    dreamerv2/
      1/
        config.yaml
        metrics.jsonl
        events.out.tfevents.*
        variables.pkl
        train_episodes/
        eval_episodes/
```

The source plot loader recursively finds `*.jsonl`, then interprets the last
three directories before each file as `task`, `method`, and `seed`. Therefore
`LOG_ROOT/atari_pong/dreamerv2/1/metrics.jsonl` is valid, while
`LOG_ROOT/experiment/atari_pong/dreamerv2/1/metrics.jsonl` is not valid for the
unmodified loader. Empty, malformed, or metric-incomplete files are skipped or
reported; an entirely empty input directory can fail before loading. Use the
helper before plotting.

`metrics.jsonl` is append-only JSON Lines. Each row has an integer-like
`step` and the scalar metrics emitted in that logger flush, for example
`eval_return`, `eval_length`, `train_return`, `loss`, or replay counters. Image
and video values are not written to JSONL. Training uses `train_` and `eval_`
prefixes for episode/report metrics; the public API's simple custom-environment
path emits unprefixed `return` and `length` unless the caller supplies another
output. `step` is the logger counter multiplied by `action_repeat`.

TensorBoard writes event files directly in the same run log directory. Scalar
tags are under `scalars/<metric-name>`; image tags use the metric name and
videos are encoded as GIF summaries when possible. The JSONL and TensorBoard
outputs are independent enough that scalar inspection can still work when a
video encoder is unavailable. See [logging and artifacts](references/logging-and-artifacts.md)
for the exact output classes and lifecycle.

## Comparing runs

Use one `--indir` for a root containing task/method/seed runs, or several input
roots to compare collections. With multiple roots the loader can distinguish seed names by adding
`indir1_...`, `indir2_...`, and `--prefix True` also prefixes method names.
In this source release the parser default is actually `--prefix False`, so set
it explicitly when comparing roots if seed/method collisions matter. Select
task and method regular expressions with `--tasks` and `--methods`.

The loader drops rows missing either selected x or y column. It bins each run
before combining seeds, and pads shorter curves with their last value when
stacking. Default bins are `1e6` for Atari, `1e4` for DMC and Crafter, and
`1e5` for other task prefixes. Use an explicit `--bins` for a reproducible
comparison. `--agg std1` draws mean plus/minus one standard deviation; the
other supported curve aggregations are `none`, `per0`, `per5`, and `per25`.
Use `--add none` to avoid combined panels, or `--add mean median seeds` (and
Atari gamer/record panels where appropriate) deliberately.

Baselines are matched by regular expressions over method names, not by
`--indir`. Automatic baseline discovery expects the renderer's package-
relative scores directory and filenames ending in `_baselines.json`. Each
matching JSON document must map task names to mappings of method names to
numeric scalar scores:

```json
{
  "atari_pong": {
    "random": -20.7,
    "human_gamer": 14.6
  }
}
```

A file named simply `baselines.json` is not matched by that filename glob, and
large pre-binned result archives with `task`, `method`, `seed`, `xs`, and `ys`
records are not baseline documents. For normalized combined panels, ensure
every selected task has both the requested low and high baseline; otherwise the
renderer reports missing normalization baselines and omits those task values.
If the selected y-axis does not contain `return`, the parser clears baseline
patterns. See [plotting](references/plotting.md) for this subtle interaction.

## Outputs and validation

A successful plot creates the selected output directory, writes `curves.png`
and `curves.pdf`, and writes the binned run records to `runs.json` before
plotting. `pdfcrop` is optional; without it the PDF remains usable and the
renderer prints an install hint. TensorBoard reads the run root, not the plot
output:

```sh
tensorboard --logdir "$LOG_ROOT"
python - <<'PY'
import pandas as pd
frame = pd.read_json("/absolute/path/to/run/metrics.jsonl", lines=True)
print(frame[['step', 'eval_return']].dropna().tail())
PY
```

For a bounded, non-rendering check, use:

```sh
python /path/to/evaluation/scripts/plot_help.py --help
python /path/to/evaluation/scripts/plot_help.py --print-command \
  --indir "$LOG_ROOT" --outdir "$PLOT_ROOT"
```

Before handing off results, record the selected x/y columns, input roots,
regexes, bin width, aggregation, baseline patterns, and the exact `runs.json`
path. Do not claim a comparison succeeded when a run was skipped for missing
metrics or when all normalization baselines were absent.

## Troubleshooting handoff

Start with [evaluation troubleshooting](references/troubleshooting.md). It
covers no metrics, nested directories, empty runs, baseline regex mismatch,
missing pandas/matplotlib, missing ffmpeg, TensorBoard paths, invalid boolean
or list arguments, and the difficult case of comparing incomplete run roots.
The complete plotting flag table is in [plotting](references/plotting.md); the
artifact schema and TensorBoard fallback behavior are in [logging and artifacts](references/logging-and-artifacts.md).
