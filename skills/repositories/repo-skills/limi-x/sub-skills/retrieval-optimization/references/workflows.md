# Workflows

These recipes are safe to read first and only run once you have a local checkpoint, a retrieval-enabled config list, and the data already in memory or on disk.

## 1) Choose a retrieval profile

The shipped retrieval templates are all sample-retrieval profiles. Use them as the starting point for tuning.

| Profile | Task | Retrieval style | Distilled defaults |
| --- | --- | --- | --- |
| `cls-16m` | Classification | Sample retrieval | `calculate_sample_attention=true`, `calculate_feature_attention=false`, `retrieval_len=389`, `use_cluster=true`, `cluster_num=22`, `use_threshold=false`, `use_dynamic=false`, `mixed_method="min"`, `threshold=0.85`, `dynamic_ratio=0.4`, `sub_feature_ratio=1` |
| `cls-2m` | Classification | Sample retrieval | `calculate_sample_attention=true`, `calculate_feature_attention=false`, `retrieval_len="dynamic"`, `use_cluster=true`, `cluster_num=47`, `use_threshold=true`, `use_dynamic=true`, `mixed_method="max"`, `threshold=0.95`, `dynamic_ratio=0.5`, `sub_feature_ratio=1` |
| `reg-16m` | Regression | Sample retrieval | `calculate_sample_attention=true`, `calculate_feature_attention=false`, `retrieval_len="dynamic"`, `use_cluster=true`, `cluster_num=45`, `use_threshold=false`, `use_dynamic=true`, `mixed_method="max"`, `threshold=0.85`, `dynamic_ratio=0.35`, `sub_feature_ratio=1` |
| `reg-2m` | Regression | Sample retrieval | `calculate_sample_attention=true`, `calculate_feature_attention=false`, `retrieval_len="dynamic"`, `use_cluster=true`, `cluster_num=50`, `use_threshold=true`, `use_dynamic=true`, `mixed_method="max"`, `threshold=0.67`, `dynamic_ratio=0.45`, `sub_feature_ratio=1` |

Selection rules:
- Use `subsample_type="sample"` and `use_type="only_sample"` for the shipped retrieval profiles.
- All shipped retrieval profiles use `retrieval_before_preprocessing=false`.
- If you want mixed sample+feature attention, enable both attention flags and expect higher memory pressure.
- If you are on a constrained GPU, prefer the smaller checkpoint family and reduce `retrieval_len` before adding more trials.
- If you are on CPU, switch to a non-retrieval config; retrieval is not supported there.

## 2) Safe Optuna tuning flow

1. Load a retrieval-enabled config list into memory.
2. Deep-copy the list before tuning; the search loop mutates `retrieval_config` in place for each trial.
3. Prepare `args` with at least `device_id` and `model_path`.
4. Optionally add search overrides such as `cluster_num_min`, `cluster_num_max`, `threshold_min`, `threshold_max`, `sample_ratio_min`, `sample_ratio_max`, `dynamic_ratio_min`, `dynamic_ratio_max`, or fixed values like `cluster_num`, `threshold`, `dynamic_ratio`, `sample_ratio`, and `mixed_method`.
5. Create `RetrievalSearchHyperparameters(args, trainX, trainy, testX, testy)`.
6. Call `.search(metric=..., n_trials=..., inference_config=..., task_type=...)`.
7. Save the returned best params into a new config copy.
8. Run a final evaluation only after the tuned config is stable.

Practical cautions:
- The current search helper accepts `attention_score`, but the search path does not use it directly.
- The current search helper returns `sub_feature_ratio=1`; tune feature subsampling elsewhere if you truly need feature retrieval.
- The current search helper does not rewrite `use_threshold` or `use_dynamic` into the config, so make sure the base config flags already match the tuning plan.
- For regression, the objective is the returned `R2` score even if you pass another metric string.

## 3) Example: preview the search space without running inference

This helper is safe and does not load a checkpoint.

Run it from the repository root:

```bash
python sub-skills/retrieval-optimization/scripts/preview_retrieval_search_space.py --profile cls-2m --json
```

Use `--config <local_retrieval_config.json>` if you want to validate a config list before tuning.

## 4) Example: tune retrieval parameters from a local checkpoint

Do not run this until your local checkpoint, tensors, and retrieval config list are ready.

```python
from copy import deepcopy

from retrieval_extension.retrieval_search_space.inference_search import RetrievalSearchHyperparameters

args = {
    "device_id": 0,
    "model_path": "<local_checkpoint.ckpt>",
    "cluster_num_min": 10,
    "cluster_num_max": 50,
    "threshold_min": 0.5,
    "threshold_max": 1.0,
    "dynamic_ratio_min": 0.1,
    "dynamic_ratio_max": 0.5,
}

config_list = deepcopy(local_retrieval_config_list)
search = RetrievalSearchHyperparameters(
    args,
    X_train,
    y_train,
    X_test,
    y_test,
)

best_params, best_value = search.search(
    metric="AUC",
    n_trials=20,
    inference_config=config_list,
    task_type="cls",
)
```

### Patch the tuned config

After the search, merge the best params into a fresh config copy before you persist it.

```python
from copy import deepcopy

final_config = deepcopy(config_list)
for item in final_config:
    item["retrieval_config"].update(best_params)
```

## 5) When to stop and route elsewhere

- If you need to build or validate the JSON schema itself, route to `../configuration-preprocessing/SKILL.md`.
- If you need the underlying predictor call or data-shape handling, route to `../predictor-inference/SKILL.md`.
- If you are looping over benchmark datasets or using `search_space_sample_num`, route to `../benchmark-cli/SKILL.md`.
