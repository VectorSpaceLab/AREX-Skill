# Model Workflows

Use these recipes to turn model-library tasks into reliable timm code. Keep initial validation offline with `pretrained=False`; switch to `pretrained=True` only after selecting an exact model or pretrained tag and confirming cache/network expectations.

## Discover a Model Name

```python
import timm

candidates = timm.list_models('*convnext*')
weighted = timm.list_pretrained('*convnext*')
```

Recommended discovery sequence:

1. Start broad with `list_models('*family*')`.
2. Narrow by implementation module with `list_models(module='resnet')` when the family is known.
3. Use `list_pretrained('*family*')` or `list_models('*family*', pretrained=True, include_tags=True)` when weights are required.
4. Validate an exact architecture with `timm.is_model(name)` and an exact weighted identifier with `timm.is_model_pretrained(name)`.
5. Inspect candidate cfgs with `timm.get_arch_pretrained_cfgs(arch)` to compare tags, input sizes, licenses, datasets, and sources.

## Create an Offline Classification Model

```python
import torch
import timm

model = timm.create_model('resnet18', pretrained=False, num_classes=5)
model.eval()

input_size = model.pretrained_cfg.get('input_size', (3, 224, 224))
x = torch.randn(1, *input_size)
with torch.inference_mode():
    y = model(x)
print(y.shape)  # usually torch.Size([1, 5])
```

This is the safest pattern for CI, repro scripts, and agent-generated examples because it does not download weights.

## Load Pretrained Weights

```python
import timm

model = timm.create_model('resnet50', pretrained=True, cache_dir='./model-cache')
model.eval()
```

Guidelines:

- Use `list_pretrained('resnet50*')` before relying on a specific pretrained tag.
- Prefer exact tagged names such as `resnet50.a1_in1k` when reproducibility matters.
- Set `cache_dir` for controlled CI or shared-cache environments.
- Expect Hugging Face Hub, URL, or local-file resolution depending on the model cfg.
- Authentication and network issues are environment concerns; do not mask them with unrelated model changes.

## Adapt Classifier Classes

```python
model = timm.create_model('mobilenetv3_large_100', pretrained=True, num_classes=12)
```

When `pretrained=True` and `num_classes` differs from the pretrained cfg, timm drops the pretrained classifier weights listed in `pretrained_cfg['classifier']` and loads the rest of the backbone with relaxed strictness. For embeddings, set `num_classes=0`:

```python
model = timm.create_model('resnet50', pretrained=False, num_classes=0)
features = model(torch.randn(2, 3, 224, 224))
```

## Adapt Input Channels

```python
model = timm.create_model('resnet18', pretrained=True, in_chans=1)
```

For pretrained loading, timm uses the cfg `first_conv` entry to adapt first-convolution weights from 3 channels when possible. If adaptation is unsupported, timm drops that weight and initializes the layer randomly. For non-RGB preprocessing details, read `model.pretrained_cfg` and route transform construction to `data-pipelines`.

Use `pretrained_cfg_overlay` when the model should advertise custom input normalization or dimensions:

```python
model = timm.create_model(
    'resnet18',
    pretrained=False,
    in_chans=1,
    pretrained_cfg_overlay={
        'input_size': (1, 224, 224),
        'mean': (0.5,),
        'std': (0.5,),
    },
)
```

## Control Pooling and Unpooled Features

Pooled embedding, classifier removed:

```python
model = timm.create_model('resnet50', pretrained=False, num_classes=0)
y = model(torch.randn(2, 3, 224, 224))  # often [batch, num_features]
```

Unpooled final map for many CNNs:

```python
model = timm.create_model('resnet50', pretrained=False, num_classes=0, global_pool='')
y = model(torch.randn(2, 3, 224, 224))  # often [batch, channels, h, w]
```

Post-construction reset:

```python
model.reset_classifier(0)      # remove classifier, keep pooling
model.reset_classifier(0, '')  # remove classifier and disable pooling when supported
```

Some families have early pooling or non-standard feature axes, so verify output shapes instead of assuming CNN-like `[N, C, H, W]`.

## Use `forward_features` and `forward_head`

```python
model = timm.create_model('vit_base_patch16_224', pretrained=False)
model.eval()

x = torch.randn(1, 3, 224, 224)
with torch.inference_mode():
    hidden = model.forward_features(x)
    logits = model.forward_head(hidden)
    embedding = model.forward_head(hidden, pre_logits=True)
```

`forward_features` bypasses the classifier and often global pooling. `forward_head` applies the head path and can return pre-logit embeddings for models that support it.

## Create a Multi-Scale Feature Backbone

```python
model = timm.create_model(
    'resnet50',
    pretrained=False,
    features_only=True,
    out_indices=(1, 2, 4),
)
model.eval()

print(model.feature_info.channels())
print(model.feature_info.reduction())
features = model(torch.randn(1, 3, 224, 224))
for feat in features:
    print(feat.shape)
```

Feature-backbone notes:

- Default `features_only=True` selects up to five levels when available.
- `out_indices` is model-specific; inspect `feature_info` rather than hardcoding strides.
- Negative indices can select from the end for helper APIs and many feature flows.
- `output_stride` can request dilation-based stride reduction on supported CNNs, but not every architecture supports every stride.
- `feature_cls='getter'` uses models with `forward_intermediates()` support where available; `feature_cls='fx'` uses FX graph extraction and has tracing limitations.

## Use `forward_intermediates` When Available

Many hierarchical and transformer-like families expose `forward_intermediates()` for flexible intermediate extraction:

```python
model = timm.create_model('vit_base_patch16_224', pretrained=False)
if hasattr(model, 'forward_intermediates'):
    output, intermediates = model.forward_intermediates(
        torch.randn(1, 3, 224, 224),
        indices=(-2, -1),
        output_fmt='NCHW',
    )
```

The index mapping is model-specific. For non-hierarchical transformers, indices often correspond to blocks; for hierarchical CNN-like models, they often correspond to stem and stage outputs.

## Load Local Checkpoints

Use `checkpoint_path` for a local checkpoint after the model is initialized:

```python
model = timm.create_model(
    'resnet18',
    pretrained=False,
    num_classes=12,
    checkpoint_path='checkpoint.pth',
)
```

Use this when the architecture and desired constructor kwargs are known. If the checkpoint has a wrapper key, different classifier shape, or different naming convention, expect missing/unexpected key diagnostics and consider adapting the checkpoint before loading.

## Scriptable, Exportable, and No-JIT Routing

```python
model = timm.create_model('resnet18', pretrained=False, scriptable=True)
model = timm.create_model('resnet18', pretrained=False, exportable=True)
model = timm.create_model('resnet18', pretrained=False, no_jit=True)
```

- `scriptable=True` asks timm layers to favor TorchScript scripting compatibility.
- `exportable=True` asks timm layers to favor trace/ONNX-style export compatibility.
- `no_jit=True` avoids optional JIT-scripted layer implementations.
- These flags are routing hints, not universal guarantees. For actual ONNX, TorchScript, or deployment work, cross-link to `export-and-interoperability`.
