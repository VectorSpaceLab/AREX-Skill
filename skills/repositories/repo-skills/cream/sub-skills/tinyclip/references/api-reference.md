# TinyCLIP API Reference

## Purpose

Read this when you need the verified public `open_clip` API surface used by TinyCLIP.
The inspection environment confirmed the distribution and the main constructors.

## Verified package facts

- Distribution: `open_clip_torch`
- Import name: `open_clip`
- Version observed during inspection: `2.0.2`
- `open_clip.factory.list_models()` returned 9 registered model configs including `RN50` and the TinyCLIP variants.

## Verified signatures

From `open_clip.factory`:

- `create_model(model_name, pretrained='', precision='fp32', device=torch.device('cpu'), jit=False, force_quick_gelu=False, pretrained_image=False, cache_dir=None, args=None)`
- `create_model_and_transforms(model_name, pretrained='', precision='fp32', device=torch.device('cpu'), jit=False, force_quick_gelu=False, pretrained_image=False, image_mean=None, image_std=None, cache_dir=None, args=None)`
- `get_model_config(model_name)`
- `get_tokenizer(model_name)`
- `list_models()`
- `load_exp(name, device='cpu')`
- `load_model(name, device='cpu')`

## Useful model-config facts

TinyCLIP config files live in `src/open_clip/model_configs/` and include model names such as:

- `TinyCLIP-ViT-39M-16-Text-19M`
- `TinyCLIP-ViT-8M-16-Text-3M`
- `TinyCLIP-ResNet-30M-Text-29M`
- `TinyCLIP-ResNet-19M-Text-19M`
- `TinyCLIP-ViT-61M-32-Text-29M`
- `TinyCLIP-ViT-40M-32-Text-19M`

## Notes from inspection

- `pretrained='openai'` loads the corresponding OpenAI checkpoint path when available.
- `pretrained_image=True` only works for timm-backed visual towers.
- `args` can carry TinyCLIP pruning flags such as `prune_image`, `prune_text`, `sparsity_warmup`, `start_sparsity`, and `target_sparsity`.

## What to avoid

Do not copy the original JSON config paths into runtime instructions. The generated skill should refer to the model names and the bundled inspection script instead.
