# Evaluation troubleshooting

## No metrics or missing columns

1. Check each expected run directory with `find "$ROOT" -name metrics.jsonl
   -type f -print`.
2. Ensure the file is non-empty and has one JSON object per line. A valid
   minimal fixture is `{"step": 1000, "eval_return": 1.0}`.
3. Run `plot_help.py --validate-layout --indir "$ROOT"`; it reports invalid
   JSON, empty files, and the final three path components.
4. Read the actual columns with pandas. The built-in workflow normally emits
   `eval_return`, but the public API path normally emits `return`; select
   `--yaxis return` for that path or configure a custom output.
5. If the requested x or y column is absent, the source loader skips that run
   without producing a curve. `--find-keys` is not a flag; the plot program
   prints keys as part of its normal startup.

A logger does not write a row when `write()` has no buffered metrics. Check
that an episode or scheduled training log was reached and that the process
flushed output. `config.yaml` and `variables.pkl` do not imply a non-empty
metrics file.

## Wrong nested directory layout

The loader assigns metadata from the last three directories before each
`metrics.jsonl`, regardless of directory names. It expects:

```text
INDIR/task/method/seed/metrics.jsonl
```

If runs are under `INDIR/experiment/task/method/seed/metrics.jsonl`, pass the
`experiment` directory as `--indir`, or reorganize into separate roots. Do not
solve this with a task regex: the parser may already be interpreting `method`
as the task. Multiple roots are supported, and root indexes are added to seed
names to prevent collisions.

## Empty and incomplete runs

Empty files are skipped. An incomplete last JSON line is ignored so a crashed
writer can still be inspected; an invalid earlier line causes the file to be
reported invalid and skipped. A file with valid JSON but no selected x/y
columns is also skipped. When comparing multiple directories, keep the
`Loading N of M runs` and `Loaded K runs` messages and inspect
`<outdir>/runs.json`; a successful exit with fewer runs is not a complete
comparison. Use `--methods`/`--tasks` filters only after validating the
unfiltered root.

When one seed stops early, stacking pads it with its last binned value. That
is source behavior, not evidence of continued environment interaction. Prefer
`--agg none` or record each seed's maximum step when analyzing incomplete
runs.

## Baseline regex mismatch or missing files

Default baseline patterns are `d4pg`, `rainbow_sticky`, `human_gamer`, and
`impala`. They are regular expressions matched against discovered method
names. `--baselines 'random' 'human_gamer'` selects those names; it does not
load arbitrary JSON files from `--indir`.

Discovery is package-relative and only scans filenames ending in
`_baselines.json`; in this source layout it searches a `scores/` directory
beside the `dreamerv2` package, not the repository-root `scores/` directory.
The repository's `scores/baselines.json` therefore neither sits in the searched
location nor matches the implementation's glob. Expected content is a JSON
object mapping a task to a method-to-number mapping. Precomputed `scores/*.json`
curve archives with `xs`/`ys` are not baselines. If a normalized panel reports
missing low/high baselines, remove that panel via `--add none` or provide both
scores for every task; do not treat missing normalization as zero.

Also note that the parser removes baseline patterns whenever `--yaxis` does
not contain `return`. This is correct for loss/replay plots. For return plots,
look at the printed baseline names and widen a regex only after confirming the
intended method.

## pandas or Matplotlib unavailable

The source renderer imports `matplotlib`, selects the non-GUI `Agg` backend,
and imports `pandas` before parsing arguments. Install compatible packages in
the package's environment, then rerun:

```sh
python -c 'import pandas, matplotlib; print(pandas.__version__, matplotlib.__version__)'
python /path/to/evaluation/scripts/plot_help.py --renderer-help
```

Do not copy `common/plot.py` into a runtime skill or run it from the original
checkout as a workaround. `plot_help.py --validate-layout` uses only the
standard library and can distinguish bad files/layout from missing plotting
dependencies. The compatible inspection evidence used TensorFlow 2.6-era
packages plus pandas and Matplotlib; newer environments may need their own
compatibility testing.

## Missing ffmpeg and GIF summaries

`TensorBoardOutput` invokes `ffmpeg` only for rank-4 video summaries. A
missing executable or failed encoder causes the logger to print
`GIF summaries require ffmpeg in $PATH.` and attempts an image summary
fallback. Scalar JSONL logging and scalar TensorBoard summaries can still
work. Verify independently:

```sh
command -v ffmpeg || echo 'ffmpeg unavailable'
python - <<'PY'
import pandas as pd
print(pd.read_json('/absolute/run/metrics.jsonl', lines=True).tail())
PY
```

If scalar logging is missing too, investigate logdir permissions, process
termination before flush, or a custom output list; ffmpeg is not the likely
cause. Unsupported channel counts or malformed video arrays are separate
shape errors and may not reach the fallback.

## TensorBoard path confusion

Point TensorBoard at the common ancestor that contains run logdirs, not at
`curves.png`, `runs.json`, or a single JSONL file:

```sh
tensorboard --logdir /absolute/log-root
```

For a single run, use its logdir. For a collection, use the parent. Confirm
that event files are present with `find "$ROOT" -name 'events.out.tfevents.*'`.
JSONL and event outputs can be independently configured, so use pandas for
JSONL when events are absent. If the event file is in a cloud URI, the logger
uses TensorFlow's writer path handling, while the JSONL output uses local
`pathlib` semantics; verify that the selected URI is supported by both outputs
before relying on them together.

## Invalid boolean/list arguments

Boolean flags accept exactly `True` or `False` (capitalized). Examples:

```sh
--subdir False --prefix True --ylimticks False
```

List flags consume all following values until the next option. Use quoted
regexes and keep pair lists even-length:

```sh
--tasks 'atari_.*' --methods 'dreamer.*' \
--labels dreamerv2 'DreamerV2' --colors dreamerv2 '#377eb8'
```

An odd number of `--labels` or `--colors` values triggers an assertion. A
missing value, unknown aggregation mode, unsupported `--add` name, or malformed
numeric range is a command-line error; rerun `--help` and start from a minimal
command with only `--indir`, `--outdir`, `--xaxis`, and `--yaxis`.

## Broken console launcher

The installed `dreamerv2` entry point calls `train.main`, which resolves
`configs.yaml` relative to `sys.argv[0]`. In this source release the launcher
therefore looks beside the installed executable and can fail before training.
This is unrelated to evaluation, but if a user is collecting a new run,
route to the training skill and use `python -m dreamerv2.train` with an
explicit logdir. Do not claim the console launcher is a valid workaround.
