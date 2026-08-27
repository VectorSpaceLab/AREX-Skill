# Inference, TTA, and Analysis

Use this reference when implementing `BaseInferencer` subclasses, adding MMEngine test-time augmentation, or reporting model complexity with `mmengine.analysis`.

## BaseInferencer Workflow

`BaseInferencer` standardizes inference into four phases:

1. `preprocess(inputs, batch_size, **kwargs)` turns user inputs into iterable batches.
2. `forward(batch, **kwargs)` calls `model.test_step(batch)` under `torch.no_grad()` by default.
3. `visualize(inputs, preds, **kwargs)` returns visualization artifacts or placeholders.
4. `postprocess(preds, visualization, return_datasamples, **kwargs)` returns the final dictionary or task-specific result object.

Subclass requirements:

| Requirement | Guidance |
| --- | --- |
| `_init_pipeline(cfg)` | Return a callable that converts one raw input into the item expected by the collate function and model. |
| `visualize(...)` | Implement even when visualization is disabled; returning an empty list is acceptable for non-visual tasks. |
| `postprocess(...)` | Convert predictions into JSON-serializable dict/list outputs unless `return_datasamples=True` is requested. |
| `preprocess_kwargs`, `forward_kwargs`, `visualize_kwargs`, `postprocess_kwargs` | Class attributes must be sets, and their keys must be disjoint. Duplicate keys raise an import-time assertion. |
| `model` argument | Accepts a config path string, model name from a downstream metafile, `Config`, `ConfigDict`, plain dict, or `None` when weights contain config. |
| `weights` argument | Loads checkpoint weights during initialization; avoid URL weights unless the user explicitly allows network access. |
| `device` argument | Defaults to `mmengine.device.get_device()` when omitted; set explicitly for deterministic CPU/GPU behavior. |

Default input handling:

- A single non-list input becomes a one-item list.
- A string that points to a directory can expand into contained files when the backend supports `isdir`.
- `preprocess()` chunks inputs by `batch_size`, maps the pipeline over each item, and applies the initialized collate function.
- If config has no test dataloader `collate_fn`, `pseudo_collate` is the fallback.
- Unknown call kwargs raise `ValueError`; add them to exactly one `*_kwargs` set and thread them into the matching phase.

Minimal custom inferencer shape:

```python
from mmengine.infer import BaseInferencer

class ToyInferencer(BaseInferencer):
    preprocess_kwargs = {'normalize'}
    forward_kwargs = set()
    visualize_kwargs = {'show'}
    postprocess_kwargs = {'topk'}

    def _init_pipeline(self, cfg):
        return lambda item: {'inputs': item, 'data_samples': None}

    def visualize(self, inputs, preds, show=False, **kwargs):
        return []

    def postprocess(self, preds, visualization, return_datasamples=False, topk=1, **kwargs):
        if return_datasamples:
            return {'predictions': preds, 'visualization': visualization}
        return {'predictions': [dict(pred) for pred in preds], 'visualization': visualization}
```

Route visualizer backend and logging details to `../runtime-utilities-and-visualization/SKILL.md`.

## Test-Time Augmentation Contract

`BaseTTAModel` wraps a normal model and implements `test_step()` for multi-augmentation batches. It does not call `forward()`; subclasses generally implement only `merge_preds(data_samples_list)`.

Input contract after TTA transforms and `pseudo_collate`:

```python
batch = {
    'inputs': [
        [sample1_aug1, sample2_aug1],
        [sample1_aug2, sample2_aug2],
    ],
    'data_samples': [
        [sample1_meta_aug1, sample2_meta_aug1],
        [sample1_meta_aug2, sample2_meta_aug2],
    ],
}
```

`BaseTTAModel.test_step()` converts that into one batch per augmentation, calls `self.module.test_step(data_aug)` for each augmentation, zips predictions by original sample, and passes a list like this into `merge_preds()`:

```python
[
    (sample1_pred_aug1, sample1_pred_aug2),
    (sample2_pred_aug1, sample2_pred_aug2),
]
```

TTA implementation rules:

- `module` may be an already-built `nn.Module` or a model config dict built through `MODELS`.
- Wrapped modules must implement `test_step`.
- If `data_preprocessor` is passed to `BaseTTAModel` with a module config, it overwrites the wrapped model's preprocessor config.
- `merge_preds()` returns one merged prediction per original sample.
- For data-element predictions, create a new data sample or clone-like object before setting merged fields; do not mutate one augmentation prediction in place unless the task owns that convention.
- For tensor/dict predictions, average scores or merge boxes/masks according to task semantics, then preserve the evaluator's expected fields.

Config pattern for Runner test-time augmentation:

```python
tta_model = dict(type='MyTTAModel', module=model)
tta_pipeline = [...]  # task-specific transform stack that returns lists per augmentation
test_dataloader = dict(dataset=dict(pipeline=tta_pipeline), ...)
```

`PrepareTTAHook(tta_cfg)` wraps `runner.model` in `before_test` by setting `tta_cfg['module'] = runner.model` and building the configured TTA model. `build_runner_with_tta(cfg)` requires both `cfg.tta_model` and `cfg.tta_pipeline`, replaces the test dataset pipeline, builds the runner, and registers `PrepareTTAHook`. Treat this helper as experimental and route full Runner config assembly to `../runner-and-training/SKILL.md`.

The original project example used a downstream classification config, remote weights, and external task packages. For generated skills, prefer a tiny local `BaseTTAModel` smoke like `scripts/tta_smoke.py` unless the user explicitly asks for a downstream OpenMMLab project integration.

## Model Complexity Analysis

Primary imports:

```python
from mmengine.analysis import get_model_complexity_info
from mmengine.analysis import FlopAnalyzer, ActivationAnalyzer
```

`get_model_complexity_info(model, input_shape=None, inputs=None, show_table=True, show_arch=True)` returns a dictionary with numeric and formatted fields:

| Key | Meaning |
| --- | --- |
| `flops`, `flops_str` | Estimated FLOPs as a number and formatted string. |
| `activations`, `activations_str` | Estimated activation count as a number and formatted string. |
| `params`, `params_str` | Parameter count as a number and formatted string. |
| `out_table` | Rich table text for per-module statistics when enabled. |
| `out_arch` | Model architecture text annotated with complexity when enabled. |

Usage rules:

- Provide exactly one of `input_shape` or `inputs`; setting neither or both raises `ValueError`.
- Use `inputs` when the model needs multiple tensors, scalars, dict-like values, or a task-specific forward signature.
- Use `input_shape=(C, H, W)` for single-tensor models; multi-input shape is a tuple of shape tuples.
- Analysis uses PyTorch JIT tracing-style behavior through `FlopAnalyzer` and `ActivationAnalyzer`; dynamic Python control flow, unsupported operators, or non-standard inputs can produce incomplete counts.
- `FlopAnalyzer(...).unsupported_ops()` and `.uncalled_modules()` can reveal missing operator handlers or modules not reached by the sample inputs.
- Add or override analyzer operator handles only when the task has a justified formula for that operator.
- Run complexity checks on representative CPU-sized inputs before reporting numbers from large GPU models.

Minimal analysis pattern:

```python
import torch
import torch.nn as nn
from mmengine.analysis import get_model_complexity_info

model = nn.Sequential(nn.Conv2d(3, 4, 1), nn.ReLU(), nn.Flatten(), nn.Linear(16, 2))
result = get_model_complexity_info(model, inputs=torch.randn(1, 3, 2, 2), show_table=False, show_arch=False)
print(result['flops_str'], result['params_str'])
```

## Optional Dependency and Runtime Limits

- `BaseInferencer` can load downstream task metafiles only when that downstream package is installed and registered.
- Remote configs, URLs, and checkpoint downloads should not be used in generated skill scripts; ask the user before network access.
- TTA examples in downstream libraries may depend on MMCV transforms and task-specific data sample classes; keep generic MMEngine guidance focused on the wrapper contract.
- Complexity analysis may warn or undercount unsupported operators; report limitations alongside numbers rather than treating FLOPs as exact.
- Visual output, progress bars, GPU inference, and distributed test execution are runtime concerns; keep model/evaluator contracts valid on CPU first.
