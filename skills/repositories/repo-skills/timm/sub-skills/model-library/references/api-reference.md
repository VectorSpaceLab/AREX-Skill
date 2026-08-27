# Model Library API Reference

This reference distills the timm 1.0.28.dev0 public model-library APIs used for model discovery, creation, pretrained config inspection, and weight loading. The installed package exposes 1293 `list_models()` entries and 1713 `list_pretrained()` entries in the inspected environment.

## Public Imports

```python
import timm
from timm import create_model, list_models, list_pretrained, get_pretrained_cfg
from timm.models import is_model, is_model_pretrained, get_arch_pretrained_cfgs
```

The top-level `timm` package re-exports the common registry and factory functions. `timm.models` also exposes lower-level helpers such as `model_entrypoint`, `list_modules`, `get_pretrained_cfg_value`, `split_model_name_tag`, `FeatureInfo`, `FeatureListNet`, `FeatureDictNet`, and `FeatureHookNet`.

## Discovery APIs

| API | Signature | Purpose | Notes |
| --- | --- | --- | --- |
| `list_models` | `list_models(filter='', module='', pretrained=False, exclude_filters='', name_matches_cfg=False, include_tags=None)` | Return sorted architecture names. | `filter` and `exclude_filters` accept shell-style wildcards. `module` limits to model implementation modules such as `resnet` or `vision_transformer`. |
| `list_pretrained` | `list_pretrained(filter='', exclude_filters='')` | Return sorted pretrained identifiers. | Equivalent to `list_models(pretrained=True, include_tags=True)`, so names may include tags like `architecture.tag`. |
| `is_model` | `is_model(model_name)` | Check whether an architecture exists. | Tag suffixes are ignored for architecture membership. |
| `is_model_pretrained` | `is_model_pretrained(model_name)` | Check whether a specific architecture or `architecture.tag` has weights. | Use exact tagged names when selecting non-default weights. |
| `list_modules` | `list_modules()` | List registry modules that own model entrypoints. | Useful for narrowing discovery to a family. |
| `get_arch_pretrained_cfgs` | `get_arch_pretrained_cfgs(model_name)` | Return all pretrained cfgs for an architecture. | Keys include tag-qualified identifiers when available. |

Examples:

```python
import timm

all_resnets = timm.list_models('*resnet*')
pretrained_resnets = timm.list_pretrained('*resnet*')
tagged_vits = timm.list_models('vit_*', pretrained=True, include_tags=True)
small_resnet_module = timm.list_models(module='resnet', exclude_filters='*101*')
```

## Model Creation

`timm.create_model` signature:

```python
def create_model(
    model_name,
    pretrained=False,
    pretrained_cfg=None,
    pretrained_cfg_overlay=None,
    checkpoint_path=None,
    cache_dir=None,
    scriptable=None,
    exportable=None,
    no_jit=None,
    **kwargs,
): ...
```

| Argument | Use | Common pitfalls |
| --- | --- | --- |
| `model_name` | Architecture, `architecture.tag`, `hf-hub:org/repo`, or `local-dir:path` identifier. | Unknown architecture raises `RuntimeError: Unknown model (...)`. Bad tags raise an invalid pretrained tag error while resolving cfg. |
| `pretrained` | Load registered or external pretrained weights. | May download from Hugging Face Hub or URL sources. Keep `False` for offline smoke tests. |
| `pretrained_cfg` | Explicit config object, dict, or tag string. | Do not set it when using `hf-hub:` model names; the factory asserts because Hub config is loaded from the source. |
| `pretrained_cfg_overlay` | Override values in the resolved pretrained cfg. | Useful for custom `input_size`, `num_classes`, `mean`, `std`, `first_conv`, or `classifier`; wrong values can break weight adaptation or preprocessing. |
| `checkpoint_path` | Load a local checkpoint after initialization. | This is a post-init load via timm helpers, separate from `pretrained=True`. Key mismatches are checkpoint compatibility issues, not registry failures. |
| `cache_dir` | Override download/cache directory for Hub and URL checkpoints. | Use when isolating cache for CI or avoiding default user cache locations. |
| `scriptable` | Build with layer config intended for TorchScript scripting. | Not all architectures are scriptable. Some tests exclude families known to fail TorchScript. |
| `exportable` | Build with layer config intended for tracing or ONNX-style export. | Export support is model-dependent; route full export work to `export-and-interoperability`. |
| `no_jit` | Disable JIT-scripted layers where timm has optional scripted implementations. | Can improve compatibility at the cost of optimized scripted components. |
| `**kwargs` | Model constructor and build kwargs, with `None` values pruned before dispatch. | Unsupported kwargs can fail for specific architectures. Prefer tested kwargs from this reference. |

Common creation kwargs:

| Kwarg | Effect |
| --- | --- |
| `num_classes=N` | Replaces/adapts the classifier for `N` classes. `num_classes=0` removes the classifier for feature embeddings. |
| `in_chans=C` | Changes input channel count. Pretrained loading attempts first-conv adaptation when possible. |
| `global_pool='avg'`, `'max'`, `'avgmax'`, `''` | Controls classifier pooling when the model supports it. Empty string disables pooling for unpooled features in many CNNs. |
| `features_only=True` | Wraps the model as a multi-scale feature backbone. |
| `out_indices=(...)` | Selects feature levels for `features_only=True`. Negative indices are supported by feature helpers. |
| `output_stride=8` or `16` | Requests dilated-conv stride reduction on supported CNN families. Some models only support stride 32. |
| `feature_cls='list'`, `'dict'`, `'hook'`, `'fx'`, `'getter'` | Selects feature extraction wrapper behavior for advanced feature extraction. |

## Pretrained Configuration

`PretrainedCfg` fields include weight locations, metadata, input/data config, and model adaptation hints:

| Field group | Keys |
| --- | --- |
| Weight source | `url`, `file`, `state_dict`, `hf_hub_id`, `hf_hub_filename`, `source`, `custom_load` |
| Identity | `architecture`, `tag`, `description`, `origin_url`, `paper_name`, `paper_ids`, `license`, `notes` |
| Input/data | `input_size`, `test_input_size`, `min_input_size`, `fixed_input_size`, `interpolation`, `crop_pct`, `test_crop_pct`, `crop_mode`, `mean`, `std` |
| Head/adaptation | `num_classes`, `label_offset`, `label_names`, `label_descriptions`, `pool_size`, `test_pool_size`, `first_conv`, `classifier` |

Access patterns:

```python
import timm

cfg = timm.get_pretrained_cfg('resnet50')
cfg_dict = cfg.to_dict() if cfg is not None else {}
input_size = timm.get_pretrained_cfg_value('resnet50', 'input_size')
model = timm.create_model('resnet50', pretrained=False)
model_cfg = model.pretrained_cfg
```

`pretrained_cfg_overlay` replaces fields after cfg resolution:

```python
model = timm.create_model(
    'resnet50',
    pretrained=False,
    num_classes=12,
    in_chans=1,
    pretrained_cfg_overlay={
        'input_size': (1, 224, 224),
        'mean': (0.5,),
        'std': (0.25,),
        'num_classes': 12,
    },
)
```

## Weight Loading Resolution

When `pretrained=True`, timm resolves the weight source in this priority order:

1. `state_dict` embedded in `pretrained_cfg`.
2. Local `file` in `pretrained_cfg`.
3. Hugging Face Hub ID when available and `huggingface_hub` is installed.
4. URL checkpoint.
5. No source: raises a runtime error telling the caller to use `pretrained=False`.

Classifier and input-channel adaptation during pretrained loading:

- If `in_chans != 3` and `pretrained_cfg['first_conv']` is set, timm tries to adapt the first convolution weights. If adaptation is unsupported, that weight is dropped and strict loading is relaxed.
- If requested `num_classes` differs from `pretrained_cfg['num_classes']`, classifier weights listed in `pretrained_cfg['classifier']` are removed and strict loading is relaxed.
- If `label_offset > 0`, classifier weights and bias are sliced to remove offset labels when class counts match.

## Name Sources

`timm.create_model` parses these model-name sources:

| Form | Meaning |
| --- | --- |
| `resnet50` | Registry architecture, optionally with the default pretrained tag when `pretrained=True`. |
| `resnet50.a1_in1k` | Registry architecture plus explicit pretrained tag. |
| `hf-hub:org/model` | Load model configuration and weights from Hugging Face Hub. Legacy `hf_hub:` is normalized to `hf-hub:`. |
| `local-dir:path` | Load model configuration from a local directory with timm-compatible metadata. |

## No-Download Smoke Check

Use the bundled script for a safe creation/forward pass:

```bash
python sub-skills/model-library/scripts/model_smoke_check.py --model resnet18 --num-classes 7
```

It uses `pretrained=False` by default, creates a tiny random input from `model.pretrained_cfg['input_size']`, runs inference, and prints the output shape.
