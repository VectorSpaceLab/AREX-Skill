# Metrics and utilities

This page collects the operational guidance for metrics, run directories, reproducibility, and device selection.

## Metric selection

`parse_metrics()` accepts these names, case-insensitively:

- `edit_distance`
- `bleu`
- `mean_average_precision`

Use the metric that matches the task:

| Task | Suggested metric | Why |
| --- | --- | --- |
| OCR or short text extraction | `edit_distance` | Penalizes character-level differences. Lower is better. |
| Free-form text generation | `bleu` | Compares generated text against reference text. |
| Object detection | `mean_average_precision` | Measures detection quality across IoU thresholds. |

### Notes on the built-in metric classes

- `EditDistanceMetric` normalizes the edit distance by the longer of the prediction and target string.
- `BLEUMetric` uses `evaluate.load("bleu")` and may need local cache or network access the first time it is loaded.
- `MeanAveragePrecisionMetric` is class-agnostic in the current implementation and returns `map50:95`, `map50`, and `map75`.

## Tracking metric history

`MetricsTracker` is the light-weight history store used by Maestro training helpers.

Recommended pattern:

```python
from maestro.trainer.common.metrics import MetricsTracker, parse_metrics

metric_objects = parse_metrics(["edit_distance", "bleu"])
tracker = MetricsTracker.init([metric.name for metric in metric_objects])
tracker.register("edit_distance", epoch=1, step=10, value=0.05)
tracker.register("bleu", epoch=1, step=10, value=0.67)
```

Helpful methods:

- `describe_metrics()` returns the registered metric names.
- `get_metric_values(metric, with_index=True)` returns the full `(epoch, step, value)` history.
- `get_metric_values(metric, with_index=False)` returns only numeric values.
- `as_json(output_dir, filename)` writes a JSON file and creates the output directory if needed.

## Plotting

`save_metric_plots(training_tracker, validation_tracker, output_dir)` builds one plot per metric name and averages repeated values by epoch.

Use it after a run if you want a simple visual history without building custom plotting code.

## Run directories

`create_new_run_directory(base_output_dir)` creates the next numeric subdirectory under the base directory.

Behavior:

- existing numeric directories are scanned
- non-numeric directories are ignored
- the returned path is absolute
- the directory is created before the path is returned

Use it for outputs such as `runs/` or `experiments/` when you want sequential numbering instead of timestamps.

## Reproducibility

`ensure_reproducibility(seed, disable_cudnn_benchmark=True, avoid_non_deterministic_algorithms=True)` is the shared seed helper.

Recommended usage:

```python
from maestro.trainer.common.utils.seed import ensure_reproducibility

ensure_reproducibility(42)
```

Important details:

- `seed=None` skips RNG seeding but still applies the deterministic torch flags unless you disable them.
- `torch.cuda.manual_seed_all()` is called when CUDA is available.
- `torch.use_deterministic_algorithms(True)` can expose unsupported ops or slow a run down; turn it off only if the workflow explicitly allows non-determinism.

## Device selection

`parse_device_spec()` accepts these values:

- `auto`
- `cpu`
- `cuda`
- `cuda:N`
- `mps`
- a prebuilt `torch.device`

`auto` prefers CUDA, then MPS, then CPU.

Use `device_is_available()` when you need to check that a parsed device is really usable on the current host.

### Practical device rules

- Use `auto` for general user-facing commands.
- Use `cuda:N` only when you know the index exists.
- Use `cpu` for inspection and smoke tests.
- Treat `mps` as a valid syntax even when the backend may not be present.

## Bundled checks

- `scripts/validate_jsonl_dataset.py` catches JSONL layout problems before training.
- `scripts/smoke_coco_vlm_adapter.py` checks that COCO parsing and formatter callbacks still agree.

These scripts are intended for quick local validation, not for downloads or long training runs.
