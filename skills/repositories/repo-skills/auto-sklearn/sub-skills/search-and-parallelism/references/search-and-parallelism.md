# Search spaces, resources, Dask, and SMAC callbacks

This reference covers the search-control layer of auto-sklearn 0.16.0.dev0. The Python package imports as `autosklearn`.

## Constructor knobs owned by this sub-skill

The classifier, regressor, and AutoSklearn2 classifier expose the following relevant arguments at construction time:

| Argument | Typical value | Effect and cautions |
|---|---:|---|
| `time_left_for_this_task` | seconds, default `3600` | Total wall-clock search budget. Longer budgets usually improve search quality. |
| `per_run_time_limit` | seconds or `None` | Cutoff for one model evaluation. If omitted, auto-sklearn derives a value. If too close to total time, it may be capped so at least two model runs can occur. |
| `memory_limit` | MB, default `3072` | Per model-evaluation memory cap. In parallel search, plan for about `n_jobs * memory_limit` plus parent/Dask overhead. `None` disables this cap. |
| `n_jobs` | `None`, `1`, positive int, or `-1` | Number of parallel fit jobs. `None`/`1` behaves as one worker; `-1` maps to all detected CPUs. It controls fitting/search, not estimator `predict()` speed. |
| `dask_client` | `distributed.Client` or `None` | User-created Dask client. If supplied, auto-sklearn wraps it as `UserDask` and does not close it. |
| `include` | `dict[str, list[str]]` | Restricts search to listed component IDs for listed pipeline steps. Incompatible with `exclude`. |
| `exclude` | `dict[str, list[str]]` | Removes listed component IDs from otherwise broad search. Incompatible with `include`. |
| `get_smac_object_callback` | callable or `None` | Advanced override that returns a SMAC facade. Use for ROAR/random search and successive halving. |
| `smac_scenario_args` | dict or `None` | Additional SMAC Scenario values. Some core keys are protected and ignored; budget/time/memory overrides produce warnings. |
| `get_trials_callback` | callable or SMAC callback | Called after each SMAC run with `(smbo, run_info, result, time_left)`; returning `False` stops optimization. |
| `disable_progress_bar` | bool | Useful for non-interactive logs. |

`AutoSklearn2Classifier` also controls its policy selection internally; route AutoSklearn2 portfolio and metadata maintenance details to the metadata sub-skill.

## Built-in `include` / `exclude` structure

`include` and `exclude` accept a dictionary keyed by pipeline step. Only use component IDs valid for the current estimator family.

```python
include = {
    "classifier": ["random_forest", "extra_trees"],
    "feature_preprocessor": ["no_preprocessing"],
}

exclude = {
    "classifier": ["libsvm_svc"],
    "feature_preprocessor": ["kernel_pca"],
}
```

Rules:

- Do not pass both `include` and `exclude`.
- Use `classifier` only with `AutoSklearnClassifier`/`AutoSklearn2Classifier`.
- Use `regressor` only with `AutoSklearnRegressor`.
- Component IDs are the Python module filenames without `.py`.
- Use `include` when the user wants a small, interpretable, or fast search; use `exclude` when only a few components are unacceptable.
- Route custom component authoring and component skeletons to [custom-components](../../custom-components/SKILL.md). This sub-skill only uses component IDs.

### Common component IDs

| Step | Valid IDs from installed/source inspection |
|---|---|
| `classifier` | `adaboost`, `bernoulli_nb`, `decision_tree`, `extra_trees`, `gaussian_nb`, `gradient_boosting`, `k_nearest_neighbors`, `lda`, `liblinear_svc`, `libsvm_svc`, `mlp`, `multinomial_nb`, `passive_aggressive`, `qda`, `random_forest`, `sgd` |
| `regressor` | `adaboost`, `ard_regression`, `decision_tree`, `extra_trees`, `gaussian_process`, `gradient_boosting`, `k_nearest_neighbors`, `liblinear_svr`, `libsvm_svr`, `mlp`, `random_forest`, `sgd` |
| `feature_preprocessor` | `densifier`, `extra_trees_preproc_for_classification`, `extra_trees_preproc_for_regression`, `fast_ica`, `feature_agglomeration`, `kernel_pca`, `kitchen_sinks`, `liblinear_svc_preprocessor`, `no_preprocessing`, `nystroem_sampler`, `pca`, `polynomial`, `random_trees_embedding`, `select_percentile_classification`, `select_percentile_regression`, `select_rates_classification`, `select_rates_regression`, `truncatedSVD` |
| `data_preprocessor` | Usually leave unconstrained unless you know the internal data preprocessing graph. Public docs expose this as a step but ordinary disabling/extension decisions should route to data or custom-component guidance. |
| `balancing` | `balancing` |

## Resource planning patterns

### Single-worker baseline

Use this when reproducibility, low RAM use, or debugging matters more than throughput:

```python
automl = autosklearn.classification.AutoSklearnClassifier(
    time_left_for_this_task=1800,
    per_run_time_limit=180,
    memory_limit=4096,
    n_jobs=1,
    tmp_folder="./autosklearn-tmp/run-001",
    delete_tmp_folder_after_terminate=False,
    seed=1,
)
```

Notes:

- With one local job and no user Dask client, auto-sklearn uses a single-threaded Dask facade and a `fork` multiprocessing context for model evaluation.
- `fork` can look memory hungry because child processes inherit the parent process address space. If this matters, use a guarded parallel or user-Dask pattern below so auto-sklearn switches to the safer `forkserver` context.

### Single-machine parallel search with `n_jobs`

```python
if __name__ == "__main__":
    automl = autosklearn.classification.AutoSklearnClassifier(
        time_left_for_this_task=7200,
        per_run_time_limit=600,
        memory_limit=3072,   # per job
        n_jobs=4,
        tmp_folder="./autosklearn-tmp/parallel-run",
        seed=5,
    )
    automl.fit(X_train, y_train, dataset_name="my_dataset")
```

Checklist:

- Put data loading and estimator construction under `if __name__ == "__main__":` or in functions called from that guard.
- Total memory may approach `4 * 3072 MB` plus parent/Dask overhead in this example.
- Ensemble building is not directly controlled by `n_jobs`; tune ensemble size and disk/model limits separately.
- `predict(..., n_jobs=...)` is a separate prediction-time setting and does not reuse the constructor `n_jobs`.

### User-managed Dask client

```python
from dask.distributed import Client, LocalCluster

if __name__ == "__main__":
    cluster = LocalCluster(
        n_workers=4,
        processes=True,
        threads_per_worker=1,
        memory_limit=0,  # auto-sklearn/pynisher handles model memory
    )
    client = Client(cluster)
    try:
        automl = autosklearn.classification.AutoSklearnClassifier(
            time_left_for_this_task=7200,
            per_run_time_limit=600,
            memory_limit=3072,
            n_jobs=1,           # ignored for worker count when dask_client is supplied
            dask_client=client,
            tmp_folder="./shared/autosklearn-run",
            seed=7,
        )
        automl.fit(X_train, y_train, dataset_name="my_dataset")
    finally:
        client.close()
        cluster.close()
```

`LocalDask` versus `UserDask` behavior:

- If `dask_client is None`, auto-sklearn uses `LocalDask(n_jobs=...)`; `LocalDask` creates clients as a context manager and closes them after use.
- If `dask_client` is supplied, auto-sklearn uses `UserDask(client)`; it reuses the same client and leaves cleanup to the caller.
- In both cases, workers must be able to access the same training/model files in `tmp_folder`.

### Distributed workers / scheduler

For multi-node workers, create the Dask scheduler/workers outside auto-sklearn and pass a connected `Client`. Use one thread per worker. Dask worker commands should set worker daemon behavior so workers may launch child model-evaluation processes, and memory management should not fight auto-sklearn's own `memory_limit`. The operational requirements are:

- same Python package environment on all workers,
- shared filesystem for `tmp_folder` and model/prediction outputs,
- main-guarded client script,
- explicit `client.close()` and worker cleanup,
- one worker CPU per concurrent model evaluation plus CPU for the scheduler/client.

## Thread oversubscription guard

Before starting Python, prefer:

```bash
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

auto-sklearn uses threadpool controls during model building, but not necessarily during inference/scoring. These environment variables prevent a run with `n_jobs=4` from becoming `4 * many_BLAS_threads`.

## SMAC strategy callbacks

The default search uses SMAC. Use `get_smac_object_callback` only when the user explicitly needs an alternate optimizer/intensifier or detailed SMAC customization.

The installed callback call signature is:

```python
def callback(
    scenario_dict,
    seed,
    ta,
    ta_kwargs,
    metalearning_configurations,
    n_jobs,
    dask_client,
    multi_objective_algorithm,
    multi_objective_kwargs,
):
    ...
```

Return a SMAC facade object. Keep the callback import-heavy parts inside the callback so a future script can import user code without requiring SMAC objects at module import time.

### ROAR / random-search pattern

```python
def get_random_search_object_callback(
    scenario_dict,
    seed,
    ta,
    ta_kwargs,
    metalearning_configurations,
    n_jobs,
    dask_client,
    multi_objective_algorithm,
    multi_objective_kwargs,
):
    from smac.facade.roar_facade import ROAR
    from smac.scenario.scenario import Scenario

    # Required if n_jobs > 1 or the client has multiple workers.
    # Remove this guard-rail only after wrapping the caller in a main guard.
    if n_jobs > 1 or (dask_client and len(dask_client.nthreads()) > 1):
        raise ValueError("Guard the Auto-sklearn entrypoint with if __name__ == '__main__'.")

    scenario_dict["minR"] = len(scenario_dict["instances"])
    scenario_dict["initial_incumbent"] = "RANDOM"
    scenario = Scenario(scenario_dict)
    return ROAR(
        scenario=scenario,
        rng=seed,
        tae_runner=ta,
        tae_runner_kwargs=ta_kwargs,
        run_id=seed,
        dask_client=dask_client,
        n_jobs=n_jobs,
    )

automl = autosklearn.classification.AutoSklearnClassifier(
    initial_configurations_via_metalearning=0,
    get_smac_object_callback=get_random_search_object_callback,
)
```

For pure ROAR without the `minR`/`initial_incumbent` random-search tweak, instantiate `ROAR` from the unmodified `scenario_dict`.

### Successive-halving pattern

```python
def successive_halving_callback(budget_type="iterations"):
    def get_smac_object(
        scenario_dict,
        seed,
        ta,
        ta_kwargs,
        metalearning_configurations,
        n_jobs,
        dask_client,
        multi_objective_algorithm,
        multi_objective_kwargs,
    ):
        from smac.facade.smac_ac_facade import SMAC4AC
        from smac.intensification.successive_halving import SuccessiveHalving
        from smac.runhistory.runhistory2epm import RunHistory2EPM4LogCost
        from smac.scenario.scenario import Scenario

        if n_jobs > 1 or (dask_client and len(dask_client.nthreads()) > 1):
            raise ValueError("Guard the Auto-sklearn entrypoint with if __name__ == '__main__'.")

        scenario = Scenario(scenario_dict)
        initial_configurations = None
        if len(metalearning_configurations) > 0:
            initial_configurations = [scenario.cs.get_default_configuration()] + metalearning_configurations

        ta_kwargs["budget_type"] = budget_type  # "iterations", "subsample", or "mixed"
        return SMAC4AC(
            scenario=scenario,
            rng=seed,
            runhistory2epm=RunHistory2EPM4LogCost,
            tae_runner=ta,
            tae_runner_kwargs=ta_kwargs,
            initial_configurations=initial_configurations,
            run_id=seed,
            intensifier=SuccessiveHalving,
            intensifier_kwargs={
                "initial_budget": 10.0,
                "max_budget": 100,
                "eta": 2,
                "min_chall": 1,
            },
            n_jobs=n_jobs,
            dask_client=dask_client,
            multi_objective_algorithm=multi_objective_algorithm,
            multi_objective_kwargs=multi_objective_kwargs,
        )
    return get_smac_object
```

The example budget types supported by the repository examples are `"iterations"`, `"subsample"`, and `"mixed"`. Successive halving is an advanced workflow; combine it with explicit `include` restrictions when the total time budget is small.

## `smac_scenario_args`

`smac_scenario_args` updates the SMAC scenario after auto-sklearn creates its default `scenario_dict`. Protected keys are ignored if supplied: `abort_on_first_run_crash`, `cs`, `deterministic`, `instances`, `output-dir`, `run_obj`, `shared-model`, and `cost_for_crash`. Overriding `cutoff_time`, `memory_limit`, or `wallclock_limit` is allowed but emits warnings because these duplicate estimator-level budgets.

Prefer estimator-level `time_left_for_this_task`, `per_run_time_limit`, and `memory_limit` unless the user explicitly understands SMAC internals.

## `get_trials_callback`

Use `get_trials_callback` for lightweight logging or early stopping after each SMAC run:

```python
def stop_after_good_score(smbo, run_info, result, time_left):
    print(run_info.config.config_id, result.status, result.cost, time_left)
    if result.cost is not None and result.cost < 0.01:
        return False  # stop optimization
    return None

automl = autosklearn.classification.AutoSklearnClassifier(
    get_trials_callback=stop_after_good_score,
)
```

The callable is wrapped for SMAC if it is not already a SMAC callback object.

## Safe config generator

Use `scripts/build_search_config.py` to prepare non-executing snippets. Example:

```bash
python scripts/build_search_config.py \
  --mode parallel \
  --n-jobs 4 \
  --memory-limit 3072 \
  --include classifier=random_forest,extra_trees \
  --include feature_preprocessor=no_preprocessing \
  --ensemble-size 20
```

The script emits JSON by default and Python snippets with `--format python`; it never imports or runs auto-sklearn.
