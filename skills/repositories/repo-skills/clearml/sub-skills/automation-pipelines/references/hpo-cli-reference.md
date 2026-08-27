# clearml-param-search HPO CLI Reference

Use `clearml-param-search` when the user wants to launch hyperparameter optimization from a base ClearML Task or local script without writing a Python optimizer controller. The command creates an optimization controller and clones jobs over search ranges; do not run it unless the user confirms ClearML credentials, a safe server, and a safe execution target.

## Required Launch Shape

The CLI requires exactly one target source plus an objective scalar:

```bash
clearml-param-search \
  --project-name "automation" \
  --task-name "hpo-controller" \
  --task-id BASE_TASK_ID \
  --queue workers \
  --params-search \
    '{"name":"General/learning_rate","type":"LogUniformParameterRange","min_value":-5,"max_value":-1,"base":10}' \
    '{"name":"General/batch_size","type":"UniformIntegerParameterRange","min_value":16,"max_value":128,"step_size":16}' \
  --params-override \
    '{"name":"General/epochs","value":10}' \
  --objective-metric-title validation \
  --objective-metric-series loss \
  --objective-metric-sign min \
  --optimizer-class RandomSearch \
  --total-max-jobs 20 \
  --max-number-of-concurrent-tasks 2
```

Target source choices:

- `--task-id TASK_ID` clones an existing ClearML Task and overrides its parameters.
- `--script train.py` creates/runs from a script entrypoint; use `--queue QUEUE` for remote workers or `--local` for local execution.
- `--task-id` and `--script` are mutually exclusive; one is required.

Objective requirements:

- `--objective-metric-title` and `--objective-metric-series` must exactly match a scalar reported by the base task, for example `Logger.report_scalar(title="validation", series="loss", ...)`.
- `--objective-metric-sign` must be one of `min`, `max`, `min_global`, or `max_global`.
- Use `min`/`max` for the last reported scalar value and `min_global`/`max_global` for the best value across all reported iterations.

## Search Parameter JSON

`--params-search` accepts one or more JSON objects as separate command-line values. The validation script also accepts a JSON list so agents can keep search spaces in a file.

Every search object needs:

```json
{"name": "General/parameter_name", "type": "UniformParameterRange"}
```

Supported `type` values and required fields:

- `UniformParameterRange`: `min_value` number, `max_value` number; optional `step_size` number, `include_max_value` boolean.
- `UniformIntegerParameterRange`: `min_value` integer, `max_value` integer; optional `step_size` positive integer, `include_max_value` boolean.
- `LogUniformParameterRange`: `min_value` number, `max_value` number; optional `base` positive number, `step_size` positive number, `include_max_value` boolean.
- `DiscreteParameterRange`: `values` non-empty list.

Examples:

```json
{"name":"General/lr","type":"UniformParameterRange","min_value":0.0001,"max_value":0.1,"step_size":0.0001}
```

```json
{"name":"General/batch_size","type":"UniformIntegerParameterRange","min_value":16,"max_value":128,"step_size":16}
```

```json
{"name":"General/optimizer","type":"DiscreteParameterRange","values":["adam","sgd"]}
```

```json
{"name":"General/lr","type":"LogUniformParameterRange","min_value":-5,"max_value":-1,"base":10}
```

Name rules:

- Prefer explicit ClearML sections such as `General/lr`, `Args/lr`, or `Hydra/optimizer.lr`.
- The CLI prefixes names without `/` as `General/<name>`.
- Search parameter names must match the base task parameters the training code reads.

## Override JSON

`--params-override` accepts one or more JSON objects with a fixed value:

```json
{"name":"General/epochs","value":10}
```

Use overrides for parameters that should not be searched but must differ from the base task defaults. The CLI converts overrides to one-value discrete ranges internally.

## Offline Validation

Validate JSON before launching jobs:

```bash
python scripts/hpo_search_space_check.py \
  --params-search '[{"name":"General/lr","type":"UniformParameterRange","min_value":0.001,"max_value":0.1}]' \
  --params-override '[{"name":"General/epochs","value":10}]' \
  --objective-sign min
```

Use a file for larger spaces:

```bash
python scripts/hpo_search_space_check.py \
  --params-search search_space.json \
  --params-override overrides.json \
  --objective-sign max_global \
  --json
```

For CLI launch, pass each object separately after a single `--params-search` flag:

```bash
clearml-param-search \
  --script train.py \
  --queue workers \
  --params-search \
    '{"name":"General/lr","type":"UniformParameterRange","min_value":0.001,"max_value":0.1}' \
    '{"name":"General/batch_size","type":"UniformIntegerParameterRange","min_value":16,"max_value":64}' \
  --objective-metric-title validation \
  --objective-metric-series accuracy \
  --objective-metric-sign max
```

## Local Mode Warnings

`--local` means the HPO jobs run locally instead of on workers:

- Use `--script` with a local file entrypoint; `--local` is not a remote task packaging shortcut.
- Pass script parameters with `--args key=value other=value`; local mode uses the current environment and does not create a fresh remote Python environment.
- Confirm local data paths, packages, GPUs/CPUs, and credentials are available before launching.
- Keep `--total-max-jobs` and `--max-number-of-concurrent-tasks` small during local smoke tests.

Remote mode warnings:

- `--queue` is the worker queue for the script/jobs; ensure a ClearML Agent is listening there.
- When using `--task-id`, the base task must be cloneable and its repository/packages/docker settings must be reproducible on the worker.
- When using `--script`, provide `--project-name` and `--task-name` when default project/task names would be ambiguous.

## Objective Metric Pitfalls

HPO ranks jobs only after the objective scalar is reported. The title and series are not inferred from display names in plots; they must match the code.

```python
task.get_logger().report_scalar(title="validation", series="loss", value=loss, iteration=epoch)
```

Matching CLI flags:

```bash
--objective-metric-title validation --objective-metric-series loss --objective-metric-sign min
```

If the user says HPO never finds results or all jobs are tied, check:

- The base task reports the scalar in every trial.
- The title and series are exact, including case and punctuation.
- The sign matches the goal: lower loss uses `min`, higher accuracy uses `max`.
- The selected `_global` mode matches whether the best-over-time or final value should decide.
- Failed or stopped jobs may not produce enough objective iterations for ranking.
