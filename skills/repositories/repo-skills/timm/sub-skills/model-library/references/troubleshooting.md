# Model Library Troubleshooting

Use this guide when timm model discovery, creation, pretrained loading, local checkpoint loading, or feature extraction behaves unexpectedly.

## Unknown Model Names

Symptoms:

- `RuntimeError: Unknown model (...)`
- A user provides a paper name, Hugging Face repo ID, or old alias that does not instantiate.

Diagnosis:

```python
import timm

query = 'resnet50'
print(timm.is_model(query))
print(timm.list_models(f'*{query}*')[:20])
print(timm.list_pretrained(f'*{query}*')[:20])
```

Fixes:

- Use the exact registry architecture from `list_models()`.
- If a tag is included, split mentally as `architecture.tag`; verify the architecture with `is_model(architecture)` and the exact weighted name with `is_model_pretrained('architecture.tag')`.
- Use wildcard discovery for renamed families, for example `*vit*`, `*convnext*`, or `*efficientnet*`.
- For Hub models, use the `hf-hub:org/repo` form only when Hub access and model metadata are expected.

## Invalid or Missing Pretrained Tags

Symptoms:

- Invalid pretrained tag error for an otherwise valid architecture.
- `pretrained=True` loads a different weight set than expected.

Diagnosis:

```python
import timm

arch = 'resnet50'
print(timm.list_pretrained(f'{arch}*'))
print(timm.get_arch_pretrained_cfgs(arch).keys())
```

Fixes:

- Use `list_pretrained()` for exact `architecture.tag` identifiers.
- Prefer a tagged model name for reproducibility instead of relying on the default tag.
- If passing `pretrained_cfg='tag'`, ensure the tag exists for that architecture.
- If passing a full custom `pretrained_cfg` dict, ensure it can construct a valid `PretrainedCfg` and has correct `architecture`, `first_conv`, `classifier`, and source fields.

## Pretrained Download, Cache, Network, or HF Auth Failures

Symptoms:

- Downloads start unexpectedly.
- Hugging Face authentication or network errors.
- URL checkpoint failures or cache permission problems.

Diagnosis:

```python
import timm

cfg = timm.get_pretrained_cfg('resnet50')
print(cfg.to_dict() if cfg else None)
```

Fixes:

- Use `pretrained=False` for offline creation and shape checks.
- Set `cache_dir` in `create_model(..., cache_dir='...')` for controlled storage.
- Install and authenticate `huggingface_hub` when using private or gated Hub weights.
- Check `hf_hub_id`, `hf_hub_filename`, `url`, `file`, and `source` in the cfg to understand the chosen source.
- If no weights exist for a model, use `pretrained=False` or choose a name from `list_pretrained()`.

## Classifier or Class Count Mismatch

Symptoms:

- Missing classifier keys during pretrained loading.
- Output shape is `[batch, 1000]` when a custom dataset has fewer classes.
- Local checkpoint classifier shape mismatch.

Fixes:

```python
model = timm.create_model('resnet50', pretrained=True, num_classes=12)
```

- Pass `num_classes` at model creation for a new classifier.
- Use `num_classes=0` for embeddings with classifier removed.
- For local checkpoints, create the model with the same `num_classes` as the checkpoint or remove classifier weights before loading.
- Check `model.pretrained_cfg['classifier']` to identify classifier parameter names.

## Input Size, Channels, or Normalization Mismatch

Symptoms:

- Runtime tensor shape errors.
- Poor pretrained inference quality despite successful loading.
- Grayscale or multispectral input fails or behaves unexpectedly.

Diagnosis:

```python
model = timm.create_model('resnet50', pretrained=False)
print(model.pretrained_cfg['input_size'])
print(model.pretrained_cfg['mean'])
print(model.pretrained_cfg['std'])
print(model.pretrained_cfg['first_conv'])
```

Fixes:

- Match the model input shape to `pretrained_cfg['input_size']` unless intentionally overriding it.
- Use `in_chans=1` or another channel count at construction time.
- Use `pretrained_cfg_overlay` to keep custom `input_size`, `mean`, and `std` visible on the model.
- Route preprocessing transform construction to `data-pipelines`; this sub-skill only identifies model-side cfg values.

## Local Checkpoint Key Mismatch

Symptoms:

- Missing or unexpected keys when using `checkpoint_path`.
- Checkpoints saved from wrappers have prefixes such as `module.` or nested state dict keys.
- Classifier or stem shapes differ.

Fixes:

- Instantiate the same architecture and kwargs used to save the checkpoint.
- Ensure `num_classes`, `in_chans`, `global_pool`, and feature/classifier settings match the checkpoint.
- Clean wrapper prefixes or extract the actual `state_dict` before loading if needed.
- If the checkpoint is for feature extraction or a modified head, avoid assuming an ImageNet classifier shape.
- Route conversion and packaging workflows to `export-and-interoperability` if checkpoint surgery becomes the main task.

## Feature Shape Surprises

Symptoms:

- `features_only=True` returns fewer or more feature maps than expected.
- ViT-like models return sequence-like or same-resolution intermediates.
- Feature channel axis is not where a downstream head expects it.

Diagnosis:

```python
model = timm.create_model('resnet50', pretrained=False, features_only=True)
print(model.feature_info.channels())
print(model.feature_info.reduction())
print(model.feature_info.module_name())
```

Fixes:

- Inspect `feature_info` for each model instead of hardcoding FPN channel counts.
- Use `out_indices` to select only the required levels.
- For ViT and hybrid families, expect non-CNN-like mappings; use `forward_intermediates()` when available.
- For dense prediction, validate feature shapes with a small random input before wiring downstream heads.

## `scriptable`, `exportable`, and `no_jit` Tradeoffs

Symptoms:

- TorchScript scripting fails on a selected family.
- FX tracing or export fails despite `exportable=True`.
- Runtime behavior differs after enabling compatibility flags.

Fixes:

- Treat `scriptable=True`, `exportable=True`, and `no_jit=True` as compatibility hints passed through timm layer config.
- Start with `pretrained=False` and a small input to isolate model construction from export tooling.
- Try `no_jit=True` if scripted activations or optional JIT layers interfere.
- Switch model families if a known architecture cannot support the required export mode.
- Route full TorchScript, ONNX, and deployment debugging to `export-and-interoperability`.

## Safe Minimal Reproduction

Use the bundled no-download script first:

```bash
python sub-skills/model-library/scripts/model_smoke_check.py --model resnet18 --num-classes 7
```

If that succeeds but the target task fails, the remaining issue is usually one of: pretrained source access, transforms/data config, incompatible checkpoint keys, unsupported model-specific kwargs, or downstream feature-shape assumptions.
