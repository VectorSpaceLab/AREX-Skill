# GluonTS cross-cutting troubleshooting

## Purpose

Use this reference for install/import, optional dependency, backend, data, and command failures that cut across sub-skills. Workflow-specific details live in each sub-skill's own troubleshooting reference.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'gluonts'` | GluonTS is not installed in the active Python. | Install `gluonts` in the target environment and rerun `python -m gluonts version` or `python scripts/check_gluonts_env.py`. |
| Importing `gluonts.torch` fails | The `torch` extra or compatible PyTorch/Lightning packages are missing. | Install `pip install "gluonts[torch]"`, then run `python scripts/check_gluonts_env.py --check-torch`. |
| `python -m gluonts.shell --help` fails | The `shell` extra is missing. | Install `pip install "gluonts[shell]"`, then read `sub-skills/deployment-extensions/SKILL.md`. |
| Warning about Python `json` module speed | Faster optional JSON backend is not installed. | This is not a correctness failure. Install the `pro` extra or an `orjson`/`ujson` package only when serialization throughput matters. |
| Optional adapter import fails (`prophet`, `statsforecast`, `rpy2`, `xgboost`, etc.) | The adapter's optional dependency group is not installed, or an external runtime such as R is missing. | Read `sub-skills/deployment-extensions/references/extension-adapters.md`; install only the named extra needed by the task. |

## Backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cuda.is_available()` is `False` | CPU-only PyTorch, incompatible driver/wheel, or no GPU passthrough. | Use CPU unless the user explicitly requires GPU. If GPU is required, fix the CUDA/PyTorch/driver stack and rerun `python scripts/check_gluonts_env.py --check-torch --cuda-smoke`. |
| PyTorch training is slow or creates many batches | Default neural estimator settings are intended for real training, not smoke checks. | In examples, set `trainer_kwargs={"max_epochs": 1, "logger": False, "enable_checkpointing": False}` plus small `batch_size` and `num_batches_per_epoch`. |
| MXNet model examples fail | MXNet workflows are legacy/unverified in this skill scope. | Do not claim MXNet support from this skill alone. Prepare a separate MXNet-compatible environment before using those APIs. |

## Data and frequency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Bad target shape or missing `target` | Dataset entries do not follow GluonTS `DataEntry` conventions. | Read `sub-skills/data-pipelines/references/data-formats.md` and run `sub-skills/data-pipelines/scripts/dataset_split_smoke.py`. |
| `start` or frequency errors | `start` is not parseable as a pandas period/timestamp, or `freq` is inconsistent. | Normalize data to a regular pandas `PeriodIndex` or pass an explicit `freq` to `PandasDataset`/`ListDataset`. |
| Dynamic feature length mismatch | Known-future dynamic features do not cover the context plus prediction horizon. | Read the data-pipelines and transforms-features workflow references; assert dynamic feature arrays have the expected time dimension before training. |
| Sampler/splitter returns no instances | `min_past`, `min_future`, `past_length`, `future_length`, or item history length is incompatible. | Read `sub-skills/transforms-features/references/troubleshooting.md` and reduce context/prediction length for tiny data. |

## Evaluation failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Forecast/target iterator length mismatch | Forecasts and target series were materialized independently or reused after consumption. | Generate both iterators from the same call, materialize once if needed, and keep pair ordering intact. See `sub-skills/evaluation-backtesting/SKILL.md`. |
| Metrics are `nan` or `inf` | Constant/too-short series, invalid labels, invalid forecasts, or zero seasonal denominator. | Inspect item metrics before aggregate interpretation and use explicit `seasonality` when needed. |
| `allow_nan_forecast=False` raises forecast validation errors | Predictor emitted NaN or invalid forecast arrays. | Fix the predictor/data first; only relax evaluator flags when the task explicitly needs to audit invalid forecasts. |

## Command and deployment failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `python -m gluonts` has only `version` | This is expected; most workflows are Python APIs or `gluonts.shell`. | Use sub-skill scripts and API references for package operations. |
| Shell training cannot find a forecaster | `GLUONTS_FORECASTER` or `forecaster_name` is missing or points to a non-importable class. | Read `sub-skills/deployment-extensions/references/deployment-workflows.md`; provide a full import path to an Estimator or Predictor class. |
| Shell inference payload rejected | Payload lacks `instances`, `target`, `start`, or uses malformed configuration. | Run `sub-skills/deployment-extensions/scripts/shell_payload_validator.py` before invoking a server or batch transform workflow. |
| SageMaker/Docker/AWS command is blocked | External service, credentials, or container runtime is absent. | Stop and report the missing external prerequisite; this generated skill does not authorize credentials or infrastructure changes. |
