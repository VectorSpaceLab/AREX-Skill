# Hyperparameter tuning with HyperTuning, Hyperopt, and Ray

Use this reference when a user asks to tune RecBole parameters, generate a `hyper.test`-style file, troubleshoot Hyperopt/Ray failures, or interpret HPO outputs. Tuning runs train many models; keep defaults small until the user approves a budget.

## Public API

```python
from recbole.trainer import HyperTuning
from recbole.quick_start import objective_function

hp = HyperTuning(
    objective_function,
    space=None,
    params_file="model.hyper",
    params_dict=None,
    fixed_config_file_list=["fixed.yaml"],
    display_file=None,
    algo="exhaustive",
    max_evals=100,
    early_stop=10,
)
hp.run()
hp.export_result(output_file="hyper.result")
print(hp.best_params)
print(hp.params2result[hp.params2str(hp.best_params)])
```

Constructor choices:

- Provide exactly one search-space source: `space`, `params_file`, or `params_dict`.
- `fixed_config_file_list` holds dataset, model, evaluation, and other fixed RecBole settings.
- `display_file` can create a visualization of the search process.
- `export_result(output_file=...)` writes each tried parameter setting with valid/test results.

## Result dictionary

The default `objective_function` returns:

```python
{
    "model": model_name,
    "best_valid_score": best_valid_score,
    "valid_score_bigger": config["valid_metric_bigger"],
    "best_valid_result": best_valid_result,
    "test_result": test_result,
}
```

`HyperTuning` optimizes `best_valid_score`, using `valid_score_bigger` to decide whether larger or smaller is better.

## Parameter file syntax

Each non-empty line has three parts:

```text
parameter_name range_type range_value
```

Supported range types:

```text
learning_rate loguniform -8,0
embedding_size choice [64,96,128]
train_batch_size choice [512,1024,2048]
mlp_hidden_size choice ['[64,64,64]','[128,128]']
dropout_prob uniform 0.0,0.5
num_layers quniform 1,4,1
```

Meanings:

- `choice`: choose from a Python-list-like set of options.
- `uniform`: sample uniformly from `(low, high)`.
- `loguniform`: sample `exp(uniform(low, high))`; the bounds are log-space values.
- `quniform`: sample uniformly then quantize by `q`.

When a parameter value is itself a list (for example an MLP hidden-size list), quote that inner list inside a `choice` list.

Use the bundled helper to create and validate a template:

```bash
python scripts/recbole_hyperopt_template.py --write-template ./model.hyper
python scripts/recbole_hyperopt_template.py --params-file ./model.hyper --validate
```

## Algorithms and budget choices

`algo` can be:

- `"exhaustive"`: grid/exhaustive search. RecBole sets `max_evals` to the search-space size. This is only safe for tiny discrete spaces.
- `"random"`: random Hyperopt search. Set `max_evals` explicitly.
- `"bayes"`: Bayesian Hyperopt/TPE search. Set `max_evals` explicitly.
- a custom Hyperopt-compatible suggest function.

Agent-safe starting point:

```bash
python scripts/recbole_hyperopt_template.py \
  --run \
  --params-file ./tiny.hyper \
  --algo random \
  --max-evals 2 \
  --model BPR \
  --dataset ml-100k \
  --epochs 1 \
  --work-dir ./recbole-runs/hpo-smoke
```

The helper uses CPU and `saved=False` by default, so it is suitable for a small validation run when RecBole and the dataset are available.

## Fixed config files and inline fixed settings

Prefer fixed config files for dataset/evaluation/model settings:

```yaml
model: BPR
dataset: ml-100k
use_gpu: False
epochs: 1
show_progress: False
metrics: [Recall, MRR, NDCG, Hit, Precision]
topk: 10
valid_metric: MRR@10
```

Then run:

```python
hp = HyperTuning(
    objective_function=objective_function,
    params_file="model.hyper",
    fixed_config_file_list=["fixed.yaml"],
    algo="random",
    max_evals=10,
)
```

If writing a custom objective, merge searched parameters with fixed settings before calling RecBole:

```python
def bounded_objective(params, config_file_list=None):
    fixed = {"model": "BPR", "dataset": "ml-100k", "use_gpu": False, "epochs": 1}
    fixed.update(params)
    return objective_function(config_dict=fixed, config_file_list=config_file_list, saved=False)
```

## Ray Tune route

Ray Tune is an optional parallel/distributed tuning path. Minimal structure:

```python
import math
import ray
from ray import tune
from ray.tune.schedulers import ASHAScheduler
from recbole.quick_start import objective_function

ray.init()

config = {
    "learning_rate": tune.loguniform(math.exp(-8), math.exp(0)),
    "embedding_size": tune.choice([64, 96, 128]),
}

scheduler = ASHAScheduler(
    metric="recall@10",
    mode="max",
    max_t=10,
    grace_period=1,
    reduction_factor=2,
)

result = tune.run(
    tune.with_parameters(objective_function, config_file_list=["/absolute/fixed.yaml"]),
    config=config,
    num_samples=5,
    scheduler=scheduler,
    local_dir="./ray_log",
    resources_per_trial={"gpu": 1},
)

best_trial = result.get_best_trial("recall@10", "max", "last")
print(best_trial.config)
print(best_trial.last_result)
```

Ray GPU notes:

- Set `resources_per_trial={"gpu": 1}` or another explicit resource mapping when using GPUs.
- Ray sets `CUDA_VISIBLE_DEVICES` per trial; RecBole config still needs compatible `use_gpu` settings.
- CPU Ray trials should set `resources_per_trial={"cpu": N, "gpu": 0}` and fixed RecBole config `use_gpu: False`.

Critical path caveat:

- Ray changes the worker working directory to its trial directory under `local_dir`.
- Any relative `data_path` in RecBole config may no longer resolve.
- Fix by making `data_path` absolute and by passing absolute fixed config file paths into `tune.with_parameters`.

Bad Ray fixed config:

```yaml
dataset: ml-100k
data_path: ./dataset
```

Safer Ray fixed config:

```yaml
dataset: ml-100k
data_path: /absolute/path/to/dataset/root
```

If Ray fails with missing dataset files, first inspect whether `data_path` became relative to the Ray trial directory rather than the project directory.

## Common HPO mistakes

- Search space too large: exhaustive search over many choices can launch dozens or hundreds of trainings.
- Unbounded epochs: HPO should start with small `epochs` and a small `max_evals` until the pipeline is validated.
- Missing fixed model/dataset: `objective_function` needs enough config to build a model and dataset.
- Mixed metric direction: use RecBole `valid_metric` and `valid_score_bigger`; do not assume every metric should be maximized.
- Invalid `choice` syntax: if a chosen value is a list-like string, quote it inside the outer list.
- Missing Hyperopt or Ray dependencies: `HyperTuning` imports Hyperopt; Ray tuning requires Ray and compatible scheduler APIs.
- GPU resource mismatch: requesting Ray GPUs when no GPUs are visible, or setting RecBole `use_gpu=True` inside CPU-only Ray trials.

## Export and analysis pattern

After `hp.run()`:

```python
hp.export_result(output_file="hyper.result")
best = hp.best_params
best_key = hp.params2str(best)
best_result = hp.params2result[best_key]
print(best)
print(best_result["best_valid_result"])
print(best_result["test_result"])
```

Do not use final test metrics to choose hyperparameters; select by validation metric, then report test metrics for the selected configuration.
