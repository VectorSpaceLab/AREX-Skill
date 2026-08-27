# Benchmarking and log-analysis reference

## Model timing contract

Two repository scripts expose a similar benchmark interface:

```bash
python tools/maptr/benchmark.py CONFIG \
  --checkpoint path/to/checkpoint.pth \
  --samples 2000 --log-interval 50

python tools/analysis_tools/benchmark.py CONFIG \
  --checkpoint path/to/checkpoint.pth \
  --samples 2000 --log-interval 50
```

The positional argument is a test config. `--checkpoint` is optional in the
parser, although an unloaded/random model is not a meaningful model comparison.
`--samples` defaults to 2000, `--log-interval` to 50, and
`--fuse-conv-bn` is accepted. In the checked `tools/maptr/benchmark.py`, the
plugin is imported when the config enables it; the analysis-tools sibling does
not perform that plugin import. Both build the configured test dataset and a
single-GPU, `samples_per_gpu=1` loader, wrap the model for device 0, and call
CUDA synchronization before and after each forward pass.

The measured loop has five warm-up iterations. Timing is accumulated after
warm-up and progress lines look like:

```text
Done image [50 / 2000], fps: <number> img / s
Overall fps: <number> img / s
```

The scripts measure model-forward wall time around the already-loaded batch,
not a complete input pipeline, image decode, visualization, checkpoint load,
or video encode. The `img / s` unit means one sample containing the configured
camera views, not one individual camera image. A GPU requirement is real:
the code calls `torch.cuda.synchronize()` and wraps the model on device 0.
Although `--fuse-conv-bn` is exposed, the actual fuse call is commented out in
both checked scripts; do not report a fused result unless a separately reviewed
implementation really performed and logged the fusion.

### Source caveats to preserve in reports

The source declares `--samples` and `--log-interval` without `type=int`.
Defaults are integers, but explicitly supplied values are strings. A supplied
`--log-interval 10` can therefore fail at modulo; a supplied `--samples 100`
can fail to match the integer loop counter and run until the dataset ends.
Treat explicit numeric options as a source defect unless a locally reviewed
patch or wrapper has corrected and tested the parsing.

The overall timing path also adds the last elapsed value a second time when the
sample limit is reached, while its numerator counts post-warm-up iterations.
This is a source-level caveat, not a reason to silently correct a published
number. If exact FPS is important, use a reviewed corrected implementation and
label it as such, or report the native output with the caveat.

If the dataset has fewer than five usable samples, the warm-up policy cannot
produce a valid post-warm-up FPS. If the requested count exceeds the dataset,
the native script may never print its overall line. Record actual processed
samples and stop rather than inferring a result.

## Fair comparison checklist

Before comparing two values, require a manifest with:

```text
config + commit/version
checkpoint identity
GPU model and count
batch size and number of camera views
precision and cudnn settings
custom extension/build status
dataset split and sample count
warm-up count and timing implementation
software versions and worker settings
```

The README's reference FPS is measured on an NVIDIA RTX3090 with batch size 1
and six view images. It cannot be used as a direct baseline for another GPU,
batch size, view count, precision, config, or custom-operation build. Batch
size changes throughput semantics; GPU changes hardware; and missing extension
status can change both correctness and speed. Mark a cross-condition request
**blocked: incomparable conditions** and give the missing fields rather than
normalizing values or averaging unlike runs.

A reasonable report separates:

- **Observed:** exact native stdout, measured sample count, and elapsed/FPS
  output.
- **Derived:** arithmetic calculated from a recorded timing trace, with its
  formula.
- **Unavailable:** anything requiring missing logs, checkpoint, data, GPU, or
  extension.

## Log analyzer contract

`tools/analysis_tools/analyze_logs.py` consumes one or more line-delimited JSON
files. Every file must end in `.json`; lines without an `epoch` field are
ignored. Remaining records are grouped by epoch and metric values are collected
as per-iteration lists.

Plot a training or evaluation curve:

```bash
python tools/analysis_tools/analyze_logs.py plot_curve run.json \
  --keys mAP_0.25 loss --mode train --interval 1 --out curves.png
```

The subcommand accepts positional `json_logs` and these options:

- `--keys`: metrics, default `mAP_0.25`;
- `--title`, `--legend`, `--backend`, `--style` (default `dark`), and `--out`;
- `--mode train|eval` (default `train`);
- `--interval` (default 1).

For training mode, x coordinates are iteration numbers assembled from epoch
records. For eval mode, records are sampled every interval and x coordinates
are epochs. A requested metric absent from the selected epoch raises
`KeyError`; mismatched legends raise an assertion; an incomplete final eval
can shorten the plotted x coordinates. `--out` saves a figure and prints the
output path; without it, the script attempts an interactive display.

Summarize iteration times:

```bash
python tools/analysis_tools/analyze_logs.py cal_train_time run.json
python tools/analysis_tools/analyze_logs.py cal_train_time run.json \
  --include-outliers
```

The output names the slowest and fastest epoch, the standard deviation of
average epoch time, and average seconds per iteration. By default it drops the
first timing value from each epoch; `--include-outliers` keeps it. State this
choice in any report because data-loader startup can dominate the first value.

## Missing evidence policy

If a benchmark request supplies incompatible hardware/batch metadata or no
logs, do not execute a comparison merely because a config exists. Emit a
blocked record containing:

```text
status: blocked
reason: missing logs or incompatible benchmark conditions
available evidence: ...
required evidence: ...
recovery: provide matching logs/manifests or rerun under one fixed protocol
```

A log file that exists but contains no epoch records, lacks the requested key,
or has a different metric cadence is also insufficient. A plot generated from
one run is not evidence that two runs are comparable.
