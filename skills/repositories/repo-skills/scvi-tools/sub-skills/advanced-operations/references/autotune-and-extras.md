# Autotune, Optional Extras, and MLflow

This reference covers advanced scvi-tools operations that depend on optional packages or orchestration systems. The verified package version is `scvi-tools` 1.4.3; core imports pass, but optional extras are not guaranteed in a default install.

## Optional extras map

Install extras only when the task needs them:

- `scvi-tools[autotune]`: enables `scvi.autotune`; installs `hyperopt>=0.2`, `ray[tune]`, `scib-metrics`, and `muon`.
- `scvi-tools[mlflow]`: enables MLflow logging helpers; installs `mlflow`, `psutil`, `GPUtil`, and `nvidia-ml-py`.
- `scvi-tools[hub]`: Hugging Face Hub and DVC/S3 model sharing support.
- `scvi-tools[file_sharing]`: file transfer helpers such as `pooch`, `gdown`, `readfcs`, and `fcswrite`.
- `scvi-tools[parallel]`: `dask[array]` and `zarr` support.
- `scvi-tools[interpretability]`: `captum`, `shap`, and `decoupler`.
- `scvi-tools[dataloaders]`: advanced dataloading integrations including LaminDB, CELLxGENE Census, TileDB-SOMA, `torchdata`, and `annbatch`.
- `scvi-tools[diagvi]`: `torch_geometric` and `geomloss` for DIAGVI-related workflows.
- `scvi-tools[cuda]`, `scvi-tools[cuda13]`, `scvi-tools[tpu]`, `scvi-tools[metal]`, `scvi-tools[rapids-cuda12]`, and `scvi-tools[rapids-cuda13]`: hardware/backend-specific dependencies; verify local torch/backend compatibility before recommending them.

Fail fast with a clear install message when importing an optional area raises `ModuleNotFoundError` or a scvi-tools dependency wrapper error.

## Autotune API

Primary entry point:

```python
from ray import tune
from scvi.autotune import run_autotune
from scvi.model import SCVI

SCVI.setup_anndata(adata)
experiment = run_autotune(
    model_cls=SCVI,
    data=adata,
    metrics="elbo_validation",
    mode="min",
    search_space={
        "model_params": {"n_hidden": tune.choice([64, 128])},
        "train_params": {"max_epochs": tune.choice([20, 100])},
    },
    num_samples=4,
    scheduler="asha",
    searcher="hyperopt",
    seed=0,
    resources={"cpu": 2, "gpu": 0},
    experiment_name="scvi-autotune",
    logging_dir="./ray-results",
    save_checkpoints=False,
)
```

`run_autotune` constructs an `AutotuneExperiment`, initializes Ray, runs `experiment.get_tuner().fit()`, and stores the Ray `ResultGrid` on `experiment.result_grid`.

Important parameters:

- `model_cls`: a scvi-tools model class such as `scvi.model.SCVI`; pass the class, not an instance.
- `data`: an AnnData/MuData object already set up with `model_cls.setup_anndata`/`setup_mudata`, or a Lightning `DataModule`.
- `metrics`: string or non-empty list; the first metric controls scheduler/searcher optimization.
- `mode`: exactly `"min"` or `"max"`.
- `search_space`: dictionary with only top-level keys `"model_params"` and `"train_params"`; values are Ray Tune search-space specs.
- `scheduler`: one of `"asha"`, `"hyperband"`, `"median"`, or `"fifo"`.
- `searcher`: one of `"hyperopt"` or `"random"`.
- `resources`: per-trial resource dictionary with keys such as `"cpu"`, `"gpu"`, and `"memory"`.
- `scheduler_kwargs` and `searcher_kwargs`: override defaults passed to Ray schedulers/search algorithms.
- `scib_stage`, `scib_subsample_rows`, `scib_indices_list`, `n_jobs`, and `solver`: only relevant for scib-metrics tuning.
- `mudata_file_name`: used when MuData must be written for Ray workers because MuData cannot be pickled directly.

## Autotune validations to preserve

`AutotuneExperiment` enforces useful invariants. Mirror these checks in generated snippets or troubleshooting:

- Do not reassign immutable fields such as `model_cls`, `data`, `metrics`, `mode`, `search_space`, `num_samples`, `scheduler`, or `searcher` after construction.
- `metrics` must be a string or non-empty list; `None` and empty lists are invalid.
- `mode` must be `"min"` or `"max"`.
- `search_space` must be non-empty and may only contain `"model_params"` and `"train_params"`.
- `num_samples` must be an integer.
- `scheduler` must be one of the supported scheduler names.
- `searcher` must be `"hyperopt"` or `"random"`.
- AnnData/MuData inputs must have a recent registered data manager for the selected `model_cls`.

## scib-metrics autotune

For scib-metrics optimization, use metrics recognized by the scib callback, such as `"Total"`, `"Batch correction"`, `"Bio conservation"`, `"Silhouette label"`, `"Isolated labels"`, `"Leiden"`, `"KMeans"`, `"cLISI"`, `"iLISI"`, `"KBET"`, `"BRAS"`, `"Graph connectivity"`, and `"PCR comparison"`.

Use `scib_subsample_rows` or `scib_indices_list` for expensive datasets. If SVD or neighbor calculations are unstable, try `solver="arpack"`, `"randomized"`, or `"auto"`, and tune `n_jobs` conservatively.

## Ray and HyperOpt notes

- `run_autotune` calls `ray.init(log_to_driver=..., ignore_reinit_error=..., local_mode=...)` and sets `RAY_AIR_NEW_OUTPUT=0` by default.
- Use `ignore_reinit_error=True` when running multiple tuning jobs in one Python process and Ray is already initialized.
- Use `local_mode=True` only for debugging; Ray itself recommends debugger-based workflows for modern debugging.
- Keep `num_samples`, `max_epochs`, and `resources` small for smoke tests.
- Prefer `searcher="random"` when HyperOpt is unavailable or the search space is tiny.

## MLflow logging

MLflow logging is configured through scvi settings and activated inside the scvi training runner when `settings.mlflow_set_tracking_uri` is non-empty and `mlflow` is installed:

```python
import scvi

scvi.settings.mlflow_set_tracking_uri = "http://127.0.0.1:5000"
scvi.settings.mlflow_set_experiment = "scvi-experiments"
model.train(max_epochs=20)
```

Useful helpers in `scvi.utils`:

- `mlflow_logger(model=None, trainer=None, training_plan=None, data_splitter=None, run_id=None)`: logs trainer settings, training-plan optimizer settings, data-splitter stats, model init params, registry setup args, summary stats, and model history metrics.
- `mlflow_log_artifact(local_path, artifact_path=None, run_id=None, max_size_mb=5.0)`: checks that the file exists and only logs files below the size limit.
- `mlflow_log_table(data, artifact_file=None, run_id=None, max_size_mb=1.0)`: logs dictionaries or pandas DataFrames, adding a temporary `table_index` column for DataFrames.
- `mlflow_log_text(text, artifact_file=None, run_id=None, max_size_mb=1.0)`: logs small text artifacts.

When a training exception occurs under MLflow logging, the runner attempts to tag the run as failed, log the error type/message, and attach an `error_log.txt` artifact.
