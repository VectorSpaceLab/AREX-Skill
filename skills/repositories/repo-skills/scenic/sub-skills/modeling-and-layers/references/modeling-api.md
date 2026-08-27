# Scenic Modeling API

This reference distills the Scenic model registry, BaseModel contracts, task-base variants, and the loss/metric conventions that keep tiny smoke checks and distributed metrics correct.

## Registry and model selection

`scenic.model_lib.models.get_model_cls(model_name)` resolves a registered Scenic model name to a `Type[BaseModel]`. If the name is unknown, it raises `ValueError('Unrecognized model: ...')`.

Use the registry probe script when you need to confirm the active names before touching configs or smoke checks.

### Registered model names

| Model name | Task family | Class |
| --- | --- | --- |
| `fully_connected_classification` | classification | `fully_connected.FullyConnectedClassificationModel` |
| `simple_cnn_classification` | classification | `simple_cnn.SimpleCNNClassificationModel` |
| `axial_resnet_multilabel_classification` | multilabel classification | `axial_resnet.AxialResNetMultiLabelClassificationModel` |
| `resnet_classification` | classification | `resnet.ResNetClassificationModel` |
| `resnet_multilabel_classification` | multilabel classification | `resnet.ResNetMultiLabelClassificationModel` |
| `bit_resnet_classification` | classification | `bit_resnet.BitResNetClassificationModel` |
| `bit_resnet_multilabel_classification` | multilabel classification | `bit_resnet.BitResNetMultiLabelClassificationModel` |
| `vit_multilabel_classification` | multilabel classification | `vit.ViTMultiLabelClassificationModel` |
| `hybrid_vit_multilabel_classification` | multilabel classification | `hybrid_vit.HybridViTMultiLabelClassificationModel` |
| `mixer_multilabel_classification` | multilabel classification | `mixer.MixerMultiLabelClassificationModel` |
| `simple_cnn_segmentation` | segmentation | `simple_cnn.SimpleCNNSegmentationModel` |
| `unet_segmentation` | segmentation | `unet.UNetSegmentationModel` |

## BaseModel contract

Every Scenic model class is built around these methods and fields:

- `__init__(config, dataset_meta_data)` stores the config and dataset metadata, then constructs `self.flax_model = self.build_flax_model()`.
- `get_metrics_fn(split=None)` returns a metric function for the pmapped/trainer path.
- `get_metrics_fn_jit(split=None)` returns a metric function for jitted/global-array evaluation paths.
- `loss_function(logits, batch, model_params=None)` returns the scalar loss.
- `build_flax_model()` returns the Flax module used for `init` and `apply`.
- `default_flax_model_config()` returns the default module config used when the caller passes `config=None`.

The model constructor should not depend on a full training run. It should be possible to create a model from config + metadata and immediately run a tiny init/apply smoke check.

## Task-specific base classes

### ClassificationModel

- Batch key: `label`, with optional `batch_mask`.
- Label format: integer labels by default; one-hot labels when `dataset_meta_data['target_is_onehot']` is true.
- Default metrics: `accuracy`, `loss`.
- Loss: weighted softmax cross entropy with optional `label_smoothing` and optional `0.5 * config.l2_decay_factor * l2_regularization(model_params)`.
- Typical output shape: `[batch, num_classes]`.

### MultiLabelClassificationModel

- Batch key: `label`, with optional `batch_mask`.
- Label format: multi-hot labels when `dataset_meta_data['target_is_onehot']` is true; otherwise the integer labels are converted to one-hot for compatibility.
- Default metrics: `prec@1`, `loss`.
- Loss: weighted sigmoid cross entropy with optional `label_smoothing` and optional L2 penalty.
- Typical output shape: `[batch, ..., num_classes]`.

### EncoderDecoderModel

- Batch key: `label`, with optional `batch_mask`.
- Label format: integer tokens by default; one-hot tokens when `dataset_meta_data['target_is_onehot']` is true.
- Default metrics: `accuracy`, `loss`, `perplexity`.
- Loss: weighted softmax cross entropy with optional `label_smoothing` and optional L2 penalty.
- `batch_mask` is expanded from example-level to token-level masking when present.
- Perplexity is derived from the averaged loss and clipped to a large maximum for reporting stability.
- Typical output shape: `[batch, length, vocab_size]`.

### SegmentationModel

- Batch key: `label`, with optional `batch_mask`.
- Label format: pixel labels by default; one-hot labels when `dataset_meta_data['target_is_onehot']` is true.
- Default metrics: `accuracy`, `loss`.
- Loss: weighted softmax cross entropy with optional `label_smoothing`, optional class rebalancing, and optional L2 penalty.
- `class_rebalancing_factor` uses `dataset_meta_data['class_proportions']` when enabled.
- Global metrics are available from the model’s global-metric hook and are computed from accumulated confusion matrices.
- Typical output shape: `[batch, height, width, num_classes]`.

### RegressionModel

- Batch key: `targets`, with optional `batch_mask`.
- Default metric: `mean_squared_error`.
- Loss: weighted mean squared error with optional L2 penalty.
- Typical output shape: same shape as `targets` except for any batch-wise structure the model defines.

## Loss and metric conventions

- Losses should usually be scalar averages on the local device batch.
- Distributed gradients are averaged outside the model, so the model loss does not need to perform a cross-device reduction.
- Metrics should return `(sum_of_values, normalizer)` pairs, not local averages.
- The normalizer should count real examples, tokens, or pixels after masking, not local batch means.
- The shared metric helpers use `psum`-style aggregation so the final reported scalar is `sum / normalizer` across all devices and hosts.
- JIT metric helpers sum over global arrays rather than averaging local device results.
- `batch_mask` is optional; when present it must be shape-compatible with the leading example/token/pixel dimensions.

## Tiny smoke-check pattern

Use a tiny dummy input and check construction before any training work:

```python
model_cls = scenic.model_lib.models.get_model_cls(name)
model = model_cls(config, dataset_meta_data)
state, params = flax.core.pop(
    model.flax_model.init(rng, dummy_input, train=False), 'params')
variables = {'params': params, **state}
outputs = model.flax_model.apply(variables, dummy_input, train=False)
```

Expected shape anchors for smoke checks:

- classification: `[batch, num_classes]`
- multilabel classification: `[batch, ..., num_classes]`
- encoder-decoder: `[batch, length, vocab_size]`
- segmentation: `[batch, height, width, num_classes]`
- regression: same leading batch structure as the target tensor
