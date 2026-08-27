# Compression API Reference

This reference summarizes the NNI compression API surfaces most useful to coding agents. It is grounded in NNI compression docs and source exports, but it is intentionally self-contained.

## Import Surfaces

```python
from nni.compression.pruning import (
    LevelPruner, L1NormPruner, L2NormPruner, FPGMPruner,
    SlimPruner, TaylorPruner, LinearPruner, AGPPruner, MovementPruner,
)
from nni.compression.quantization import (
    QATQuantizer, PtqQuantizer, DoReFaQuantizer,
    BNNQuantizer, LsqQuantizer, LsqPlusQuantizer,
)
from nni.compression.distillation import (
    DynamicLayerwiseDistiller, Adaptive1dLayerwiseDistiller,
)
from nni.compression.utils import (
    TorchEvaluator, LightningEvaluator, TransformersEvaluator,
    DeepspeedTorchEvaluator, auto_set_denpendency_group_ids,
)
from nni.compression.speedup import ModelSpeedup
```

The top-level `nni.compression` package exports evaluator wrappers, while algorithm classes are exported from pruning, quantization, and distillation subpackages.

## Config List Schema

`config_list` is a list of dictionaries. Each dictionary selects modules and applies compression settings. Selection is the intersection of includes minus excludes:

- `op_names`: fully qualified module names from `model.named_modules()`.
- `op_names_re`: regular expressions matched against module names.
- `op_types`: class names for modules inheriting from `torch.nn.Module`, such as `Conv2d` or `Linear`.
- `exclude_op_names`: exact module names to remove from selected modules.
- `exclude_op_names_re`: regular expressions for module names to remove.
- `exclude_op_types`: module type names to remove.

At least one include key (`op_names`, `op_names_re`, or `op_types`) should be present in each config. If `op_names` or `op_names_re` are present and `op_types` is also present, NNI selects modules satisfying both name and type criteria.

### Targets

- `target_names`: legal compression targets, often `_input_`, `weight`, `bias`, `_output_`, or indexed/named variants such as `_input_0`, `_input_x`, `_output_0`, or `_output_logits`.
- `target_settings`: mapping from target name to target-specific settings.
- Shortcut settings: keys other than common selection keys are treated as shorthand target settings and can apply to selected targets.

### Pruning Settings

- `sparse_ratio`: float from 0 to 1; masks that fraction of a pruning target.
- `max_sparse_ratio`: float greater than 0 and at most 1; caps sparsity per target.
- `min_sparse_ratio`: float at least 0 and less than 1; lower bound per target.
- `sparse_threshold`: float threshold for metric-based pruning.
- `global_group_id`: integer or string; targets in the same group share a total sparsity objective.
- `dependency_group_id`: integer or string; targets in the same group prune compatible positions together.
- `granularity`: `default`, `in_channel`, `out_channel`, `per_channel`, or an integer list for block sparsity.
- `internal_metric_block`: integer block size for internal metric handling.
- `apply_method`: `bypass`, `mul`, or `add`.
- `align`: settings that align one target mask with another, commonly bias aligned to weight.

Prefer `sparse_ratio` for direct pruning goals. Use `sparse_threshold` only when the selected pruner's algorithm explains the threshold metric.

### Quantization Settings

- `quant_dtype`: quantized dtype string such as `int8`, or `null` when intentionally inherited or deferred.
- `quant_scheme`: `affine` or `symmetric`.
- `granularity`: `default`, `in_channel`, `out_channel`, `per_channel`, or integer list.
- `apply_method`: `bypass`, `clamp_round`, or `qat_clamp_round`.
- `fuse_names`: list of module-name groups to fuse when supported by the chosen workflow.

Quantization targets commonly include `_input_`, `weight`, and `_output_`; PTQ workflows also need calibration behavior through an evaluator.

### Distillation Settings

- `lambda`: integer or float loss weight.
- `link`: string or list of strings describing linked teacher/student targets.
- `apply_method`: `mse` or `kl`.

Distillation configs are only statically checkable to a limited degree. Tensor shapes and teacher/student compatibility must be checked in the user's model code.

## Legacy Config Notes

Some older examples used keys such as `exclude`, `sparsity`, `sparsity_per_layer`, `total_sparsity`, `max_sparsity_per_layer`, `quant_types`, and `quant_bits`. Current NNI code includes transformation logic for legacy configs, but future agents should author current-style configs using `exclude_op_*`, `sparse_ratio`, `target_names`, and `target_settings` when possible.

## Pruner Selection Guide

| Need | Candidate | Notes |
| --- | --- | --- |
| Quick sparse baseline | `LevelPruner` | Element-wise magnitude; simple but often no structural speedup. |
| Channel/filter pruning | `L1NormPruner`, `L2NormPruner`, `FPGMPruner` | Good default family for `Conv2d` or `Linear` with `out_channel`-style goals. |
| BatchNorm scale pruning | `SlimPruner` | Requires models with normalization scale parameters and training/fine-tuning. |
| Gradient-sensitive pruning | `TaylorPruner` | Needs representative training/evaluator signals. |
| Gradual pruning schedule | `LinearPruner`, `AGPPruner` | Use when a one-shot sparsity jump is too unstable. |
| Transformer fine-tuning sparsity | `MovementPruner` | Useful when weight movement during fine-tuning is the pruning signal. |

## Quantizer Selection Guide

| Need | Candidate | Notes |
| --- | --- | --- |
| No full retraining | `PtqQuantizer` | Needs calibration/evaluation data. |
| Accuracy-preserving low precision | `QATQuantizer` | Needs training or fine-tuning through an evaluator. |
| Low-bit research algorithms | `DoReFaQuantizer`, `BNNQuantizer`, `LsqQuantizer`, `LsqPlusQuantizer` | Use when the user names the method or wants an algorithm experiment. |

## Evaluator Object Contracts

### `TorchEvaluator`

Use for native PyTorch loops. Important callable contracts:

- `training_func(model, optimizers, training_step, lr_schedulers, max_steps, max_epochs)` should train the model and obey `max_steps` or `max_epochs`.
- `training_step(batch, model, *args, **kwargs)` should return loss, a tuple with loss first, or a dict containing `loss`.
- `evaluating_func(model)` should return a float metric or a dict containing `default`.
- Optimizer and scheduler constructors should be wrapped with `nni.trace` when NNI needs constructor information.

### `LightningEvaluator`

Use when the user's project already uses PyTorch Lightning. Wrap the Lightning `Trainer`, `LightningModule`, `LightningDataModule`, optimizer, and scheduler constructors with `nni.trace` where needed so NNI can reconstruct or inspect them.

### `TransformersEvaluator`

Use for Hugging Face `Trainer` workflows. Wrap the `Trainer` constructor with `nni.trace`; trace custom optimizer and scheduler constructors as well.

### `DeepspeedTorchEvaluator`

Use for native PyTorch loops under DeepSpeed. Its `training_func` should interact with the DeepSpeed engine returned to the loop and should not assume ordinary optimizer calls.

## Speedup Objects

- `ModelSpeedup(model, dummy_input, masks).speedup_model()` physically compacts a pruned PyTorch model when masks and graph shape inference are compatible.
- Quantization speedup lives under TensorRT/ONNX-oriented modules and is a deployment/backend operation, not the same as QAT or PTQ compression.

## Validator Script

Use the bundled validator for fast static checks:

```bash
python scripts/validate_config_list.py config_list.json --mode pruning
python scripts/validate_config_list.py config_list.json --mode quantization
python scripts/validate_config_list.py config_list.json --mode distillation
```

The validator intentionally does not import NNI or Torch. It catches malformed JSON, non-list configs, missing include selectors, conflicting legacy `exclude` usage, non-list selector fields, invalid sparsity bounds, invalid quantization fields, and malformed target settings. It cannot prove that module names exist in a user's model or that an evaluator trains correctly.
