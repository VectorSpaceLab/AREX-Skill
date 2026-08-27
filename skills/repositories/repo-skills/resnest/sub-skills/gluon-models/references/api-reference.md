# Gluon API Reference

This reference covers the optional MXNet Gluon API surface for ResNeSt. It is conditional: if `mxnet` is not installed, imports from `resnest.gluon` fail before any model can be constructed.

## Public imports

```python
from resnest.gluon import resnest50, resnest101, resnest200, resnest269
from resnest.gluon import get_model
from resnest.gluon.model_zoo import get_model_list
```

`get_model` is re-exported from `resnest.gluon`. `get_model_list` lives in `resnest.gluon.model_zoo`; import it from that module when you need the available-name catalog.

## Factory families

All factory functions follow this shape:

```python
factory(pretrained=False, root='~/.mxnet/models', ctx=mx.cpu(0), **kwargs)
```

Common keyword ideas passed through `**kwargs` into the Gluon `ResNet` constructor:

| Keyword | Typical use |
|---|---|
| `classes=1000` | Number of classifier output units. Use 1000 for ImageNet and pretrained weights. |
| `dilation=1`, `dilated=False` | Controls output stride for dense prediction or feature extraction variants. `dilation` values 2, 3, and 4 alter later stages. |
| `input_size=224` | Used by DropBlock shape bookkeeping and high-resolution variants. Match validation/training crop size for large models. |
| `last_gamma=True` | Initializes the last BatchNorm gamma in each bottleneck to zero when constructing a training model. |
| `dropblock_prob=<float>` | Enables DropBlock in supported ResNeSt blocks. The stock builders set `0.1` for published classifiers. |
| `use_global_stats=True` | Forces BatchNorm to use stored global statistics, useful when fine-tuning pretrained classifiers with small batches. |
| `norm_layer`, `norm_kwargs` | Advanced BatchNorm or SyncBatchNorm customization. SyncBatchNorm is only sensible in a compatible multi-device setup. |

When `pretrained=True`, keep `classes=1000` unless you are intentionally handling classifier-shape mismatch. For transfer learning with a different class count, load the base model with `pretrained=False`, initialize or load compatible parameters manually, then replace or train the classifier head.

## Model names

| Name | Builder | Main architecture choices | Published Gluon ImageNet top-1 |
|---|---|---|---|
| `resnest50` | `resnest50` | layers `[3,4,6,3]`, radix 2, cardinality 1, width 64, crop 224 | 81.04 |
| `resnest101` | `resnest101` | layers `[3,4,23,3]`, radix 2, cardinality 1, width 64, crop 256 | 82.81 |
| `resnest200` | `resnest200` | layers `[3,24,36,3]`, final dropout 0.2, crop 320 | 83.88 |
| `resnest269` | `resnest269` | layers `[3,30,48,8]`, final dropout 0.2, crop 416 | 84.53 |
| `resnest50_fast_1s1x64d` | fast ablation | radix 1, cardinality 1, width 64 | 80.35 |
| `resnest50_fast_2s1x64d` | fast ablation | radix 2, cardinality 1, width 64 | 80.65 |
| `resnest50_fast_4s1x64d` | fast ablation | radix 4, cardinality 1, width 64 | 80.90 |
| `resnest50_fast_1s2x40d` | fast ablation | radix 1, cardinality 2, width 40 | 80.72 |
| `resnest50_fast_2s2x40d` | fast ablation | radix 2, cardinality 2, width 40 | 80.84 |
| `resnest50_fast_4s2x40d` | fast ablation | radix 4, cardinality 2, width 40 | 81.17 |
| `resnest50_fast_1s4x24d` | fast ablation | radix 1, cardinality 4, width 24 | 80.97 |

All listed builders use a deep stem, average-down projection, split-attention blocks, and average-down/AVD-style ResNeSt behavior encoded in the factory. Fast variants use `avd_first=True` and the `resnetv1f_` name prefix.

## `get_model` and `get_model_list`

```python
from resnest.gluon import get_model
net = get_model('resnest50', pretrained=False, ctx=mx.cpu(0), classes=1000)

from resnest.gluon.model_zoo import get_model_list
names = list(get_model_list())
```

Behavior:

- `get_model(name, **kwargs)` lowercases `name` and dispatches only to the local ResNeSt Gluon builders listed above.
- Unknown names raise `ValueError` and include the sorted local model list in the message.
- `get_model_list()` returns the dictionary-key view of local model names; wrap it with `list(...)` or `sorted(...)` for display.
- `get_model` itself does not load arbitrary GluonCV models. The GluonCV fallback exists in the lower-level model-store function described below.

## Context (`ctx`) handling

Use an MXNet context that matches the user's backend:

```python
import mxnet as mx
ctx = mx.cpu(0)          # portable default
# ctx = mx.gpu(0)        # only if a matching MXNet CUDA build and GPU exist
net = resnest50(pretrained=False, ctx=ctx)
net.initialize(ctx=ctx)
y = net(mx.nd.random.uniform(shape=(1, 3, 224, 224), ctx=ctx))
```

The validation recipe can split batches across a list of contexts. Single-model smoke checks should use one context first; multi-GPU behavior depends on a CUDA-enabled MXNet wheel and visible devices.

## Pretrained parameter store

`pretrained=True` calls `model.load_parameters(get_model_file(name, root=root), ctx=ctx)`.

Important behavior:

- Factory default parameter root: `~/.mxnet/models`.
- Direct `model_store.get_model_file(...)` default root: `~/.encoding/models`.
- ResNeSt parameter filenames use `<model>-<first-8-sha1>.params`, for example `resnest50-bcfefe1d.params`.
- If the file exists and its SHA-1 matches, it is reused.
- If the file is missing or the SHA-1 check fails, the model store downloads a zip from the ResNeSt release-weight URL, extracts it into the root, deletes the zip, and verifies SHA-1 again.
- The `ENCODING_REPO` environment variable can override the base release URL used by the downloader. Use this only for a trusted internal mirror.
- If the final SHA-1 check fails, construction raises `ValueError` instead of silently using corrupt parameters.

Known local ResNeSt SHA-1 prefixes:

| Name | Prefix used in filename |
|---|---|
| `resnest50` | `bcfefe1d` |
| `resnest101` | `5da943b3` |
| `resnest200` | `0c5d117d` |
| `resnest269` | `11ae7f5d` |
| `resnest50_fast_1s1x64d` | `5e16dbe5` |
| `resnest50_fast_2s1x64d` | `85eb779a` |
| `resnest50_fast_4s1x64d` | `3f215532` |
| `resnest50_fast_1s2x40d` | `af3514c2` |
| `resnest50_fast_2s2x40d` | `2db13245` |
| `resnest50_fast_4s2x40d` | `b24d5157` |
| `resnest50_fast_1s4x24d` | `7318153d` |

## GluonCV fallback nuance

If `resnest.gluon.model_store.get_model_file(name, root=...)` is called directly with a name that is not in the local ResNeSt SHA map, it delegates to `gluoncv.model_zoo.model_store.get_model_file(name, root=root)`. That requires `gluoncv` to be installed and only handles parameter lookup; it does not make `resnest.gluon.get_model(name)` accept non-ResNeSt constructors.
