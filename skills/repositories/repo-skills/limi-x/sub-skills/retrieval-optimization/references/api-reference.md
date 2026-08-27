# API reference

This reference covers the retrieval-specific API surface and the retrieval keys that must stay consistent with the local config list.

## Core signatures

```python
class RetrievalSearchHyperparameters:
    def __init__(self, args, trainX, trainy, testX, testy, attention_score=None)

    def search(
        self,
        method=None,
        metric: Literal["AUC", "accuracy", "f1"] = "AUC",
        n_trials: int = 1000,
        inference_config=None,
        task_type="cls",
    )
```

```python
class InferenceAttentionMap:
    def __init__(
        self,
        model_path: str | torch.nn.Module,
        calculate_feature_attention: bool = False,
        calculate_sample_attention: bool = False,
    )

    def inference(
        self,
        X_train,
        y_train,
        X_test,
        task_type: Literal["reg", "cls"] = "cls",
        device: int | torch.device = 0,
    ) -> tuple[torch.Tensor | None, torch.Tensor | None]
```

```python
class InferenceResultWithRetrieval:
    def inference(
        self,
        X_train=None,
        y_train=None,
        X_test=None,
        dataset=None,
        attention_score=None,
        retrieval_len=2000,
        dynamic_ratio=None,
        use_cluster=False,
        cluster_num=2,
        task_type="cls",
        cluster_method="overlap",
        use_threshold=False,
        threshold=0.5,
        mixed_method="max",
        device=0,
        **kwargs,
    )
```

## Search helper behavior

| Item | Behavior |
| --- | --- |
| `method` | Accepted by the signature, but the current search path does not use it. |
| `metric` | `AUC`, `accuracy`, or `f1` for classification. Regression returns `R2` regardless of the metric string. |
| `n_trials` | Passed to Optuna as the number of trials. The study is created with `direction="maximize"`. |
| `inference_config` | Must be a JSON file path or a loaded config list. It is updated in place during search. Deep-copy before tuning if you need to preserve the original list. |
| `task_type` | `"cls"` uses `auc_metric`, `accuracy_score`, or `f1_score`. Any other value follows the regression branch and returns `r2_score`. |
| `attention_score` | Stored on the search object, but the current search loop does not consume it directly. Retrieval attention is computed through the predictor path. |

## Required `args` fields

| Key | Purpose |
| --- | --- |
| `device_id` | CUDA device index used when CUDA is available. The search helper builds `cuda:<device_id>` in that case. |
| `model_path` | Local checkpoint path passed into the predictor constructor. |
| `cluster_num_min` / `cluster_num_max` | Optional bounds that shape the search range for cluster count. |
| `threshold_min` / `threshold_max` | Optional bounds that shape the threshold search range. |
| `sample_ratio_min` / `sample_ratio_max` | Optional bounds for fixed-length retrieval when dynamic mode is off. |
| `dynamic_ratio_min` / `dynamic_ratio_max` | Optional bounds for dynamic retrieval length. |
| `cluster_num` / `threshold` / `sample_ratio` / `dynamic_ratio` / `mixed_method` / `use_cluster` / `use_threshold` / `use_dynamic` | Optional overrides that either lock a value or, if falsey in the current source behavior, leave the value searchable. |

## Search-space args consumed by the helper

The tuning helper builds retrieval parameters from a dictionary of search overrides. The search space is small and safe to preview without running the model.

| Arg key | Type / branch | Meaning |
| --- | --- | --- |
| `use_cluster` | categorical `True/False` unless a truthy override is provided | Enables clustering after top-k selection. A falsey override does not lock the flag in the current source behavior. |
| `cluster_num_min` / `cluster_num_max` | integers | Bounds used when `use_cluster` is not fixed. Defaults are 10 and 50. |
| `cluster_num` | integer | Fixed cluster count if a truthy override is provided and clustering is enabled. |
| `use_threshold` | categorical `False/True` unless a truthy override is provided | Enables threshold-based top-k selection. A falsey override does not lock the flag in the current source behavior. |
| `threshold_min` / `threshold_max` | floats | Bounds used when `use_threshold` is active and `threshold` is not fixed. Defaults are 0.5 and 1.0. |
| `threshold` | float | Fixed threshold if a truthy override is provided and thresholding is enabled. |
| `use_dynamic` | categorical `False/True` unless a truthy override is provided | Switches retrieval length to dynamic mode. A falsey override does not lock the flag in the current source behavior. |
| `sample_ratio_min` / `sample_ratio_max` | integers | Bounds used when retrieval length is not dynamic. Defaults are 200 and 500. |
| `sample_ratio` | integer | Fixed retrieval length if a truthy override is provided and dynamic mode is off. |
| `dynamic_ratio_min` / `dynamic_ratio_max` | floats | Bounds used when dynamic retrieval is active and `dynamic_ratio` is not fixed. Defaults are 0.1 and 0.5. |
| `dynamic_ratio` | float | Fixed dynamic ratio if a truthy override is provided and dynamic mode is on. |
| `mixed_method` | categorical `"max"` / `"min"` | Controls how the threshold helper respects the retrieval-length floor or cap. |

## Returned update keys

The search helper merges only these keys back into each pipeline's `retrieval_config`:

| Returned key | Meaning |
| --- | --- |
| `use_cluster` | Whether clustering is enabled for the trial. |
| `cluster_num` | Cluster count for the trial, or `None` when clustering is off. |
| `threshold` | Threshold value for cumulative-attention selection, or `None` when thresholding is off. |
| `retrieval_len` | Effective retrieval length or the string `"dynamic"`. |
| `dynamic_ratio` | Ratio used when dynamic retrieval is active, or `None` otherwise. |
| `mixed_method` | Threshold helper mode. |
| `sub_feature_ratio` | Feature subsampling ratio passed to the attention-driven subsampler. |

Note: `use_threshold`, `use_dynamic`, and `sample_ratio` are not written back by the search helper even though they affect search-space construction. Keep those flags aligned in the base config before you start tuning.

## Retrieval config keys

These are the retrieval keys observed in the shipped retrieval templates and consumed by the predictor path.

| Key | Role | Notes |
| --- | --- | --- |
| `use_retrieval` | Enables retrieval mode | Must be `true` for retrieval runs. |
| `retrieval_before_preprocessing` | Places retrieval before or after preprocessing | The shipped retrieval profiles use `false`. |
| `calculate_feature_attention` | Requests feature-attention maps | Required for feature retrieval and for mixed sample+feature retrieval. |
| `calculate_sample_attention` | Requests sample-attention maps | Required for sample retrieval. |
| `retrieval_len` | Number of retrieved samples, or `"dynamic"` | May also be a float fraction inside the retrieval inference path. |
| `subsample_type` | `"sample"` or `"feature"` | The shipped retrieval profiles use `"sample"`. |
| `use_type` | `"only_sample"` or `"mixed"` | `"mixed"` combines sample and feature attention in subsampling. |
| `use_cluster` | Cluster selected test samples | Reduces repeated work for similar test cases. |
| `cluster_num` | Number of clusters | `InferenceResultWithRetrieval.inference` also accepts `"num_class"`. |
| `use_threshold` | Use cumulative-attention thresholding | Enables `find_top_K_indice`. |
| `threshold` | Cumulative-attention threshold | Keep in the `[0, 1]` range. |
| `use_dynamic` | Turn on dynamic retrieval length | Controls whether `retrieval_len` becomes `"dynamic"`. |
| `dynamic_ratio` | Ratio used for dynamic retrieval | Used only when dynamic retrieval is active. |
| `mixed_method` | Threshold helper mode | `"max"` enforces a lower bound of retrieval length; `"min"` caps at retrieval length. |
| `sub_feature_ratio` | Feature subsampling ratio | Passed to the attention-driven subsampler. |
| `sample_ratio` | Legacy/template-only alias | Present in one shipped classification template; do not treat it as the effective search key. |

## Attention and retrieval flow

- `InferenceAttentionMap.inference(...)` runs the local model with `calculate_sample_attention` and/or `calculate_feature_attention` enabled.
- The returned feature attention is trimmed to the test portion; sample attention is returned as produced by the model path.
- `InferenceResultWithRetrieval.inference(...)` is the sample-retrieval engine.
- `sample_selection_type="AM"` means attention-map retrieval.
- `sample_selection_type="DDP"` means the distributed, non-retrieval path.
- For `task_type="cls"`, the engine relabels training labels per batch before inference and restores class order afterward.
- For `task_type="reg"`, the engine uses regression outputs directly.
