# Model and Metric Contracts

Use this reference when writing or repairing MMEngine model classes, data preprocessors, metric classes, composed evaluators, and prediction dump workflows.

## Model Class Contract

| Surface | Required behavior | Notes |
| --- | --- | --- |
| `BaseModule(init_cfg=None)` | Use for modules that need MMEngine initialization control. | Store initialization policy in `init_cfg`; call `init_weights()` through normal MMEngine flows instead of manually reinitializing parameters after runner setup. |
| `BaseModel(data_preprocessor=None, init_cfg=None)` | Supplies a default `BaseDataPreprocessor` when none is provided, or builds a preprocessor config through `MODELS`. | Pass either a dict or an already-built `nn.Module`; other types raise `TypeError`. |
| `forward(..., mode='tensor')` | Implement `loss`, `predict`, and `tensor` branches intentionally. | `BaseModel._run_forward` unpacks dict data as keyword args and list/tuple data as positional args, then appends `mode=...`. |
| `mode='loss'` | Return a dict whose values are tensors or lists of tensors. | At least one key must contain the substring `loss`, because `parse_losses()` sums keys containing `loss` for backward. |
| `mode='predict'` | Return predictions in the shape expected by the evaluator. | OpenMMLab task repos commonly use `list[BaseDataElement]`, while MMEngine itself accepts sequences of dict-like predictions for metrics. |
| `mode='tensor'` | Return raw tensor, tuple, or dict outputs for custom inference/analysis use. | This branch is not the evaluator contract; do not reuse it for validation unless metrics explicitly expect raw tensors. |
| `train_step(data, optim_wrapper)` | Default implementation preprocesses with `training=True`, calls `mode='loss'`, parses losses, updates `OptimWrapper`, and returns log vars. | Override only when custom optimization or multiple optimizers are required; preserve `optim_wrapper.optim_context(self)` and a log dict return. |
| `val_step(data)` and `test_step(data)` | Default implementation preprocesses with `training=False`, calls `mode='predict'`, and returns predictions. | Override when validation needs extra loss outputs or test-time behavior differs, but keep evaluator inputs stable. |

Minimal model pattern:

```python
from mmengine.model import BaseModel

class TinyModel(BaseModel):
    def __init__(self, data_preprocessor=None, init_cfg=None):
        super().__init__(data_preprocessor=data_preprocessor, init_cfg=init_cfg)
        ...

    def forward(self, inputs, data_samples=None, mode='tensor'):
        logits = self.backbone(inputs)
        if mode == 'loss':
            return {'loss_cls': self.loss_fn(logits, data_samples)}
        if mode == 'predict':
            return [{'pred_label': int(i)} for i in logits.argmax(dim=1)]
        if mode == 'tensor':
            return logits
        raise RuntimeError(f'Invalid mode: {mode}')
```

## Data Preprocessor Contract

`BaseDataPreprocessor` moves tensors and `BaseDataElement` objects to its tracked device recursively. `BaseModel.to()`, `.cuda()`, `.cpu()`, and device-specific methods update nested `BaseDataPreprocessor` devices along with model parameters.

`ImgDataPreprocessor` additionally handles image batches:

- Accepts a dict with `inputs`; it sets `data_samples` to `None` when absent.
- With pseudo-collated data, `inputs` may be a list of `(C, H, W)` tensors; it converts to float, optionally swaps BGR/RGB channels, normalizes, pads to `pad_size_divisor`, and stacks.
- With default-collated data, `inputs` must be a 4D NCHW tensor.
- `mean` and `std` must both be `None` or both be provided, with length 1 or 3.
- `bgr_to_rgb` and `rgb_to_bgr` cannot both be `True`.
- Three-channel mean/std require three-dimensional single-image tensors or four-dimensional batched tensors with channel dimension 3.

Use a custom preprocessor when the dataloader returns a project-specific structure, when batch augmentations must happen between collation and model forward, or when the model should receive transformed `data_samples` rather than raw dataset records.

## Loss Parsing Rules

`BaseModel.parse_losses(losses)` accepts a dict where each value is either a tensor or a list of tensors. It averages each tensor value for logging, sums list entries per key, and creates the top-level `loss` value by summing every logged key whose name contains `loss`.

Common implications:

- Use names such as `loss_cls`, `loss_bbox`, or `aux_loss`; metrics or diagnostics that are not part of backward should not include `loss` in the key unless they should contribute to optimization.
- A missing loss key makes the summed loss invalid for training even if the dict has other tensors.
- Non-tensor values in the loss dict raise `TypeError`; convert scalars to tensors on the right device.
- If a custom `train_step` bypasses `parse_losses`, it still must return a log dict compatible with Runner logging.

## Metric and Evaluator Contract

| Surface | Required behavior | Notes |
| --- | --- | --- |
| `BaseMetric(collect_device='cpu', prefix=None, collect_dir=None)` | Subclass `process()` and `compute_metrics()`; append processed, picklable results into `self.results`. | `collect_dir` is only valid with `collect_device='cpu'`. |
| `default_prefix` or `prefix` | Provide a stable namespace for metric keys. | If neither is set, MMEngine warns; composed evaluators can collide on unprefixed keys. |
| `process(data_batch, data_samples)` | Convert one batch of predictions and optional batch data into compact results. | Move or detach heavyweight tensors if storing them; avoid keeping full model outputs when only labels/scores are needed. |
| `compute_metrics(results)` | Return a dict of metric names to scalar-like values. | Do not mutate global state; `evaluate()` clears `self.results` afterward. |
| `evaluate(size)` | Collects distributed results, truncates padding to `size`, CPU-converts tensors/data elements on the main process, prefixes keys, broadcasts metrics, and clears `self.results`. | Reusing a metric after `evaluate()` requires another full set of `process()` calls. |
| `Evaluator(metrics)` | Builds or wraps one or more metrics and forwards `dataset_meta` to all of them. | `Evaluator.process()` converts `BaseDataElement` predictions to dicts before passing them to metrics. |
| `Evaluator.evaluate(size)` | Calls each metric and merges returned dicts. | Duplicate final keys raise `ValueError`; use prefixes to disambiguate. |
| `Evaluator.offline_evaluate(data_samples, data=None, chunk_size=1)` | Processes precomputed predictions without a runner. | If `data` is provided, its length must match `data_samples`. |

Minimal metric pattern:

```python
from mmengine.evaluator import BaseMetric

class Accuracy(BaseMetric):
    default_prefix = 'acc'

    def process(self, data_batch, data_samples):
        for sample in data_samples:
            self.results.append({
                'pred': int(sample['pred_label']),
                'target': int(sample['gt_label']),
            })

    def compute_metrics(self, results):
        correct = sum(item['pred'] == item['target'] for item in results)
        return {'top1': correct / max(len(results), 1)}
```

Composed evaluator pattern:

```python
from mmengine.evaluator import Evaluator

evaluator = Evaluator([
    Accuracy(prefix='cls'),
    dict(type='DumpResults', out_file_path='predictions.pkl'),
])
evaluator.process(data_samples=[{'pred_label': 1, 'gt_label': 1}], data_batch=None)
metrics = evaluator.evaluate(size=1)
# metrics contains {'cls/top1': 1.0}; DumpResults returns {} after writing predictions.
```

## DumpResults Behavior

`DumpResults(out_file_path, collect_device='cpu', collect_dir=None)` is a `BaseMetric` that writes collected predictions to a pickle file and returns an empty metrics dict.

Operational rules:

- `out_file_path` must end with `.pkl` or `.pickle`.
- Predictions are recursively moved to CPU in `process()` when they contain tensors or `BaseDataElement` objects.
- The dump path is user project output, not a skill artifact. Choose a caller-owned path and avoid overwriting important files.
- Combine `DumpResults` with scoring metrics when both saved predictions and scalar metrics are required.
- In distributed CPU collection, use `collect_dir` only with `collect_device='cpu'`; GPU collection does not accept `collect_dir`.

## Registry and Config Placement

Models and metrics are commonly registered with `MODELS` and `METRICS`, then referenced from project configs:

```python
model = dict(type='TinyModel', data_preprocessor=dict(type='ImgDataPreprocessor'))
val_evaluator = dict(type='Accuracy', prefix='val')
test_evaluator = [dict(type='Accuracy', prefix='test'), dict(type='DumpResults', out_file_path='predictions.pkl')]
```

Route config syntax, `custom_imports`, `_scope_`, and registration discovery issues to `../configuration-and-registry/SKILL.md`. Route where `model`, `val_evaluator`, and `test_evaluator` sit inside a full Runner config to `../runner-and-training/SKILL.md`.

## Safe Validation Checklist

1. Instantiate the model and call `model.data_preprocessor(batch, training=True/False)` on a tiny batch.
2. Call `model.forward(..., mode='loss')` directly and confirm the returned dict has tensor loss keys.
3. Call `model.train_step(batch, OptimWrapper(...))` only with a tiny optimizer-backed model.
4. Call `model.val_step(batch)` or `model.test_step(batch)` and inspect prediction shape before wiring an evaluator.
5. Feed two or three predictions through `Evaluator.process()` and `Evaluator.evaluate(size=...)`.
6. If dumping predictions, read the pickle back and verify tensors are CPU-resident before relying on offline evaluation.
