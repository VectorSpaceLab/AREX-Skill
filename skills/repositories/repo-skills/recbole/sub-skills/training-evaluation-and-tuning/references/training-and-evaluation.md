# Training, evaluation, save/load, case-study, and significance

This reference is CPU-first and assumes RecBole is installed in the active Python environment. It intentionally uses public APIs and bundled helper scripts rather than source-checkout scripts.

## One-model quick-start APIs

Use `run` when you may need distributed arguments; use `run_recbole` for a single-process API call.

```python
from recbole.quick_start import run, run_recbole

result = run(
    model="BPR",
    dataset="ml-100k",
    config_file_list=["example.yaml"],  # optional
    config_dict={
        "use_gpu": False,
        "epochs": 1,
        "show_progress": False,
    },
    saved=False,
    nproc=1,
)

# equivalent single-process route
result = run_recbole(
    model="BPR",
    dataset="ml-100k",
    config_file_list=["example.yaml"],
    config_dict={"use_gpu": False, "epochs": 1, "show_progress": False},
    saved=False,
)
```

Result shape:

```python
{
    "best_valid_score": float,
    "valid_score_bigger": bool,
    "best_valid_result": {"metric@k": value, ...},
    "test_result": {"metric@k": value, ...},
}
```

`objective_function(config_dict=None, config_file_list=None, saved=True)` is the HPO-compatible route and returns the same keys plus `"model"`.

## Safe CPU smoke run

Use this pattern for quick validation or examples that should not create checkpoints:

```python
safe_config = {
    "use_gpu": False,
    "epochs": 1,
    "show_progress": False,
    "log_wandb": False,
}
result = run("BPR", "ml-100k", config_dict=safe_config, saved=False)
```

Prefer the bundled helper when the user asks for a runnable script:

```bash
python scripts/recbole_train_eval_smoke.py --dry-run-config
python scripts/recbole_train_eval_smoke.py \
  --run \
  --model BPR \
  --dataset ml-100k \
  --epochs 1 \
  --work-dir ./recbole-runs/bpr-cpu-smoke
```

Notes:

- `saved=False` avoids model checkpoints. RecBole may still write logs under the process working directory; use a dedicated working directory to avoid writing to a source checkout.
- If saving is needed, set `saved=True` and provide a `checkpoint_dir` under the run directory.
- `show_progress=False` avoids progress bars in non-interactive agent logs.
- `use_gpu=False` is a valid configuration for CPU-safe examples when the selected model and dataset fit CPU budgets.

## Trainer-level reference

For advanced flows that build `Config`, datasets, dataloaders, and models manually, the trainer entry points are:

```python
best_valid_score, best_valid_result = trainer.fit(
    train_data,
    valid_data=None,
    verbose=True,
    saved=True,
    show_progress=False,
    callback_fn=None,
)

test_result = trainer.evaluate(
    eval_data,
    load_best_model=True,
    model_file=None,
    show_progress=False,
)
```

Important behavior:

- When validation data exists and `saved=True`, the best checkpoint is saved and later loaded by `evaluate(load_best_model=True)`.
- When `saved=False`, call `evaluate(..., load_best_model=False)` if evaluating a manually trained model without a saved checkpoint.
- `callback_fn(epoch_idx, valid_score)` can collect custom per-epoch telemetry.

## Evaluation settings and metric interpretation

RecBole evaluation configuration is mostly carried by `eval_args`, `metrics`, `topk`, and `valid_metric`:

```yaml
eval_args:
  group_by: user
  order: RO
  split: {RS: [0.8, 0.1, 0.1]}
  mode: full
metrics: [Recall, MRR, NDCG, Hit, Precision]
topk: 10
valid_metric: MRR@10
eval_batch_size: 4096
metric_decimal_place: 4
```

Key choices:

- `group_by`: commonly `user`; `none` disables user grouping.
- `order`: `RO` random order or `TO` temporal order.
- `split`: `RS` ratio split, or `LS` leave-one-out variants such as `valid_and_test`.
- `mode`: `full` ranking over all items, `uniN` / `popN` sampled negative ranking, or `labeled` for explicit-label evaluation.
- Ranking metrics include `Recall`, `Precision`, `Hit`, `NDCG`, `MAP`, `MRR`, `GAUC`, `ItemCoverage`, `AveragePopularity`, `GiniIndex`, `ShannonEntropy`, and `TailPercentage`.
- Value metrics include `AUC`, `MAE`, `RMSE`, and `LogLoss`.
- Do not mix ranking and value metrics in the same evaluation setting.
- `valid_metric` controls early stopping. Use `valid_score_bigger` from the result dictionary to know whether larger is better.

Dataset schema, `load_col`, field aliases, and atomic file placement are owned by the configuration/data sibling skill.

## Saving and loading model/data artifacts

To save a model checkpoint and optionally reuse processed data artifacts:

```python
from recbole.quick_start import run_recbole, load_data_and_model

save_config = {
    "use_gpu": False,
    "epochs": 1,
    "show_progress": False,
    "checkpoint_dir": "./checkpoints",
    "save_dataset": True,
    "save_dataloaders": True,
}
run_recbole(model="BPR", dataset="ml-100k", config_dict=save_config, saved=True)

config, model, dataset, train_data, valid_data, test_data = load_data_and_model(
    model_file="./checkpoints/BPR-...pth"
)
```

Expected artifact names are controlled by RecBole at runtime. Logs usually identify:

- the saved model checkpoint (`*.pth` under `checkpoint_dir`),
- the filtered dataset file when `save_dataset=True`,
- the split dataloaders file when `save_dataloaders=True`.

Verified public signature in this source version: `load_data_and_model(model_file)`. Some documentation variants mention optional dataset/dataloader file arguments; if a user relies on those, inspect the installed package signature before writing code that passes them.

Use the bundled recipe helper to validate and print the loading sequence:

```bash
python scripts/recbole_save_load_recipe.py --model-file ./checkpoints/BPR-example.pth
```

## Case-study scoring

Case studies require a saved model and the test dataloader returned by `load_data_and_model`.

```python
from recbole.quick_start import load_data_and_model
from recbole.utils.case_study import full_sort_scores, full_sort_topk

config, model, dataset, train_data, valid_data, test_data = load_data_and_model(
    model_file="./checkpoints/BPR-example.pth"
)

# External user tokens -> RecBole internal ids.
uid_series = dataset.token2id(dataset.uid_field, ["196", "186"])

# Top-k item ids and scores.
topk_scores, topk_iids = full_sort_topk(
    uid_series,
    model,
    test_data,
    k=10,
    device=config["device"],
)
external_items = dataset.id2token(dataset.iid_field, topk_iids.cpu())

# Full score matrix for selected users.
scores = full_sort_scores(uid_series, model, test_data, device=config["device"])
```

Preconditions and interpretation:

- `dataset.token2id` must know the supplied external user tokens. Unknown tokens are a data/config problem.
- `dataset.id2token` converts internal item ids back to external tokens.
- `full_sort_scores` masks the padding item and, for non-repeatable recommendation, history items by setting their scores to `-inf`.
- For large item catalogs, full-sort score matrices can be memory-heavy; use `full_sort_topk` when only top-k items are needed.

Executable helper:

```bash
python scripts/recbole_save_load_recipe.py \
  --model-file ./checkpoints/BPR-example.pth \
  --topk 10 \
  --users 196,186
```

## Grouped model runs

The grouped-run pattern loops over a comma-separated model list, calls `run(...)` once per model on the same dataset/config, collects `best_valid_result` and `test_result`, and optionally writes comparison tables. It is reference-only here because it launches many training jobs and writes result files.

Minimal pattern:

```python
models = ["BPR", "LightGCN"]
valid_rows = []
test_rows = []
for model_name in models:
    result = run(
        model_name,
        "ml-100k",
        config_file_list=["shared.yaml"],
        config_dict={"use_gpu": False, "epochs": 1, "show_progress": False},
        saved=False,
    )
    valid_rows.append({"Model": model_name, **result["best_valid_result"]})
    test_rows.append({"Model": model_name, **result["test_result"]})
```

For fair comparison, keep data split, seed policy, metrics, top-k, negative sampling/evaluation mode, and hardware settings aligned across models.

## Significance testing

The significance-test pattern repeats both models on the same list of seeds, collects each metric from `test_result`, then runs a paired t-test per common metric.

```python
import random
from scipy import stats
from recbole.quick_start import run

random.seed(2023)
seeds = [random.randint(0, 2**32 - 1) for _ in range(10)]

def collect(model, config_files):
    by_metric = {}
    for seed in seeds:
        result = run(
            model,
            "ml-100k",
            config_file_list=config_files,
            config_dict={"seed": seed, "use_gpu": False, "show_progress": False},
            saved=False,
        )
        for key, value in result["test_result"].items():
            by_metric.setdefault(key, []).append(value)
    return by_metric

ours = collect("BPR", ["ours.yaml"])
baseline = collect("NeuMF", ["baseline.yaml"])

p_values = {
    metric: stats.ttest_rel(ours[metric], baseline[metric])
    for metric in ours.keys() & baseline.keys()
}
```

Cautions:

- This is expensive by default: `run_times * number_of_models` full trainings.
- Use matched seeds; do not compare one set of random seeds against another.
- Choose `alternative` deliberately (`two-sided`, `less`, or `greater`) based on the statistical question.
- Keep all non-model settings matched, including data split and evaluation settings.

## CPU, GPU, and distributed decisions

Single-process CPU is valid and recommended for smoke tests:

```python
config_dict = {"use_gpu": False, "epochs": 1, "show_progress": False}
run("BPR", "ml-100k", config_dict=config_dict, saved=False)
```

GPU acceleration uses configuration keys such as `use_gpu: True` and `gpu_id`. Confirm CUDA availability and model/device compatibility before promising speedups.

Distributed training uses the `run` API arguments:

- `nproc`: number of processes on the current node.
- `world_size`: total number of ranks across all nodes; if `-1`, single-node `world_size` follows `nproc`.
- `ip`: master node address.
- `port`: master node port.
- `group_offset`: rank offset for the current node.

Example shape:

```python
result = run(
    "BPR",
    "ml-100k",
    config_file_list=["distributed.yaml"],
    config_dict={"use_gpu": True, "gpu_id": "0,1"},
    saved=True,
    nproc=2,
    world_size=2,
    ip="localhost",
    port="5678",
    group_offset=0,
)
```

Distributed runs are not smoke tests. Check port availability, rank offsets, node count, GPU visibility, and whether the chosen model/dataset justifies multiprocessing overhead.

## TensorBoard and Weights & Biases

RecBole can log training loss and validation score to TensorBoard directories and can log to W&B when `log_wandb=True`. For agent-safe defaults:

- leave `log_wandb` false unless the user explicitly configured credentials,
- keep run artifacts under a dedicated working directory,
- tell users to inspect TensorBoard logs from that directory if they request visual training curves.
