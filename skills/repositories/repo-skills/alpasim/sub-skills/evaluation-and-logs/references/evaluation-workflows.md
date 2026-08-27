# Evaluation workflows

## Post-evaluate a completed rollout set

The evaluation package exposes these portable module forms:

```bash
python -m eval.main \
  --asl_search_glob '<run-dir>/rollouts/**/*.asl' \
  --config_path '<run-dir>/eval-config.yaml' \
  --trajdata_cache_dir '<trajdata-cache>' \
  --usdz_glob '<scene-dir>/**/*.usdz' \
  --log-level INFO
```

The current evaluator uses `--asl_search_glob`, `--config_path`, and
`--usdz_glob` directly. The trajectory-cache argument is accepted for
compatibility with the package workflow; ensure the cache is available when
map-backed dependencies require it.

Evaluation merges the YAML into `EvalConfig`, discovers scene artifacts from the
USDZ glob, and loads run metadata from YAML files beside the evaluation config.
It filters the globbed ASLs by the `_complete` marker and fails if none are
found or if only part of the glob is marked complete. Each successful rollout
writes `metrics.parquet` beside its ASL. If `eval.video.render_video` is true,
video files are written in that same rollout directory.

Use `--log-level DEBUG` when diagnosing config resolution, artifact discovery,
worker selection, or missing message data. `num_processes` controls the worker
pool and is capped by available CPUs and the number of ASLs; use one process
for a small fixture or when isolating a failure.

## Re-evaluate a previous run

For a single run or an array-job parent, the re-evaluation module detects the
layout from `eval-config.yaml`:

```bash
python -m eval.reeval <run-dir>
```

A single job has the evaluation config at `<run-dir>/eval-config.yaml`. An
array-job parent has child directories with that file; each child is evaluated
and then the parent is aggregated. The detector reads `wizard-config.yaml` to
find the runtime image, scene cache, and scene-set path. Local re-evaluation
therefore still needs the scene cache and USDZ artifacts available at the
resolved paths.

The re-evaluation implementation invokes the evaluation and aggregation
modules as subprocesses. It stops after the first non-zero evaluation result.
It creates `aggregate/` only after the per-job evaluation phase succeeds.

A scheduler mode exists:

```bash
python -m eval.reeval <run-dir> --slurm \
  --partition cpu_short --account ACCOUNT
```

This is not a read-only operation: it creates scripts/log directories and
submits one evaluation job (or an array) plus a dependent aggregation job. Use
it only with explicit credentials, a reviewed partition/account, and a known
container/scene mount policy. For ordinary diagnosis, stay local and inspect
or adapt the generated commands rather than submitting them.

## Aggregate existing metrics

```bash
python -m eval.aggregation.main \
  --array_job_dir '<array-job-parent>' \
  --config_path '<run-dir>/eval-config.yaml'
```

Aggregation discovers job directories containing `wizard-config.yaml` and
collects `rollouts/**/metrics.parquet`. In a single-job directory it can use the
root directly. It writes `aggregate/metrics_unprocessed.parquet`,
`metrics_results.parquet`, `metrics_results.txt`, `results-summary.json`, and
`metrics_results.png`; with video enabled it also creates `aggregate/videos/`.
Relative links under the video tree point back to rollout videos.

Array jobs are combined with a deterministic UUID derived from the input run
UUIDs. If `force_same_run` is used programmatically, clip identifiers must be
unique across the source runs; duplicate clip identifiers are a data-integrity
error, not a reason to silently merge rows.

## Programmatic API

The normal post-eval path is:

```python
from eval.asl_loader import load_scenario_eval_input_from_asl
from eval.scenario_evaluator import ScenarioEvaluator

scenario_input = await load_scenario_eval_input_from_asl(
    asl_file_path, cfg, artifacts, {"run_uuid": run_uuid, "run_name": run_name}
)
result = ScenarioEvaluator(cfg).evaluate(scenario_input)
```

`ScenarioEvalResult` contains `timestep_metrics`, `aggregated_metrics`, and a
Polars `metrics_df`. `ScenarioEvaluator` constructs a `SimulationResult`,
calculates all registered scorers, and adds `eval_relevant` to identify rows
at or after policy engagement when pre-engagement removal is enabled.

Keep the runtime and post-eval paths comparable: both should consume the same
message ordering and configuration. If their metric names or row counts differ,
compare the ASL records, force-GT metadata, driver request/return pairs, map,
camera calibration, and config before comparing numerical values.

## Entrypoint issue

The installed `print-asl` and `asl-to-frames` scripts currently import
`main` from their `__main__` modules, but those modules only define parser code
under `if __name__ == "__main__"`. Their console commands fail at import time.
Use `python -m alpasim_utils.print_asl` and
`python -m alpasim_utils.asl_to_frames`, or the bundled helpers. The eval,
aggregation, and re-eval modules do define `main`, so their console wrappers
are usable when the package environment is healthy; module invocation remains
preferable in scripts and containers.
