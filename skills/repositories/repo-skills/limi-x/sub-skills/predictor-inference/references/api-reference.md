# LimiXPredictor API Reference

This reference is self-contained for future agents using the LimiX predictor API. It assumes the LimiX Python package or checkout is importable and that model/config files are local to the user's runtime environment.

## Import

```python
from inference.predictor import LimiXPredictor
```

The constructor loads the model checkpoint immediately; it is not a lazy wrapper.

## Constructor

Exact public signature to use:

```python
LimiXPredictor.__init__(
    device,
    model_path,
    inference_config,
    mix_precision=True,
    outlier_remove_std=12,
    softmax_temperature=0.9,
    mask_prediction=False,
    categorical_features_indices=None,
    inference_with_DDP=False,
    seed=0,
)
```

| Parameter | Expected value | Behavior and caveats |
| --- | --- | --- |
| `device` | `torch.device`, usually `torch.device("cuda:0")` or `torch.device("cpu")` | Controls where model tensors are moved. If `device.type == "cpu"`, retrieval configs are rejected and `mix_precision` is forced off. |
| `model_path` | String path to a local LimiX checkpoint file | The constructor calls the checkpoint loader immediately. Provide an existing local `.ckpt`; this sub-skill does not download weights. |
| `inference_config` | Local JSON path string or in-memory `list` of pipeline dictionaries | A string must point to an existing JSON file containing a non-empty list. Each pipeline is expected to contain `retrieval_config`. A missing path raises `ValueError`. |
| `mix_precision` | `bool`, default `True` | Enables autocast around model forward on CUDA. CPU inference prints that mixed precision is unsupported and disables it. |
| `outlier_remove_std` | `float`, default `12` | Accepted by the API and documented as an outlier threshold. In the current predictor path it is stored on the instance; do not rely on it as an active preprocessing switch. |
| `softmax_temperature` | `float`, default `0.9` | Classification logits are divided by this value before softmax when it differs from `1`. Lower values sharpen probabilities; higher values soften them. |
| `mask_prediction` | `bool`, default `False` | Enables feature reconstruction for MVI. The checkpoint is loaded with mask prediction enabled and `predict()` returns a tuple. |
| `categorical_features_indices` | `list[int]` or `None` | Accepted and stored, but the current predictor preprocessing does not actively use this constructor argument. Categorical handling is otherwise automatic/heuristic. |
| `inference_with_DDP` | `bool`, default `False` | Hands inference to the distributed/NCCL path. Use only in GPU distributed workflows prepared by the caller; do not enable for CPU smoke tests. |
| `seed` | `int`, default `0` | Drives preprocessing shuffles, class permutation ensembling, and torch seeds set during prediction. |

### Config selection cheat sheet

| Need | Config family | Device notes |
| --- | --- | --- |
| Classification, CPU or smallest smoke | `cls_default_noretrieval.json` | Required on CPU because retrieval is unsupported there. |
| Classification, retrieval ensemble | `cls_default_16M_retrieval.json` or `cls_default_2M_retrieval.json` | CUDA/GPU required; high-end GPUs are recommended for retrieval. |
| Regression, CPU or smallest smoke | `reg_default_noretrieval.json` | Required on CPU because retrieval is unsupported there. |
| Regression, retrieval ensemble | `reg_default_16M_retrieval.json` or `reg_default_2M_retrieval.json` | CUDA/GPU required; route retrieval tuning to the retrieval sub-skill. |
| Missing-value imputation | `reg_default_noretrieval_MVI.json` with `mask_prediction=True` | The public model table identifies MVI support for the 16M checkpoint; do not assume every checkpoint supports it. |

If a config is passed as a list and `mask_prediction=True`, the predictor may modify worker tags that are incompatible with MVI. Pass a deep copy when the original config object must be preserved.

## Prediction

Exact public signature to use:

```python
predict(
    x_train,
    y_train,
    x_test,
    task_type="Classification",  # or "Regression"
)
```

| Parameter | Expected value | Notes |
| --- | --- | --- |
| `x_train` | 2D array-like, shape `(n_train, n_features)` | NumPy arrays and pandas dataframes are accepted when convertible through scikit-learn validation. |
| `y_train` | 1D array-like, length `n_train` | Classification labels are label-encoded internally. Regression targets must be numeric. |
| `x_test` | 2D array-like, shape `(n_test, n_features)` | Must have the same feature columns as `x_train`. For MVI, pass the masked test features containing `np.nan`. |
| `task_type` | Exact string `"Classification"` or `"Regression"` | Any other value raises an unsupported-task `ValueError`. |

## Return values

| Mode | Return type | How to interpret |
| --- | --- | --- |
| Classification, `mask_prediction=False` | `np.ndarray`, shape `(n_test, n_classes)` | Row-normalized class probabilities averaged across configured estimators. Predicted labels are `np.argmax(proba, axis=1)`. Output columns follow `predictor.classes` after `predict()` runs. |
| Regression, `mask_prediction=False` | `torch.Tensor`, usually shape `(n_test,)` | Averaged numeric predictions. Convert with `pred.detach().cpu().numpy()` before NumPy metrics or denormalization. |
| Classification, `mask_prediction=True` | `(proba, reconstructed_features)` | First element is classification probabilities. Second element is a NumPy reconstructed-feature matrix for the concatenated train+test rows; slice the last `len(x_test)` rows for test imputation. |
| Regression, `mask_prediction=True` | `(pred_tensor, reconstructed_features)` | First element is the regression tensor. Second element is the reconstructed-feature matrix. The MVI recipe commonly uses regression mode and ignores the primary target prediction. |

## Useful instance state after prediction

- `predictor.classes`: classification class labels in output-column order.
- `predictor.n_classes`: number of classes seen in `y_train`.
- `predictor.n_estimators`: number of config pipelines being ensembled.

## Secondary config update method

```python
set_inference_config(inference_config, softmax_temperature=None, seed=None)
```

Use this only when a workflow intentionally sweeps configs on the same loaded checkpoint. It accepts the same path-or-list `inference_config` contract as the constructor, optionally updates `softmax_temperature` and `seed`, then rebuilds preprocessing pipelines. Retrieval hyperparameter search itself is outside this sub-skill.
