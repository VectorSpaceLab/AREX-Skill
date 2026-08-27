---
name: encoders-preprocessing
description: "Choose segmentation_models_pytorch encoders/backbones, configure
  weights, and retrieve preprocessing parameters without relying on the source
  repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Encoders and Preprocessing

Use this sub-skill when a task asks how to choose an SMP encoder/backbone, list supported encoders, use `tu-` timm universal names, migrate deprecated `timm-` requests, choose a DPT-compatible encoder, or configure `get_preprocessing_params` / `get_preprocessing_fn`.

## Start Here

- For native and ported encoders, use `segmentation_models_pytorch.encoders.get_encoder_names()` to list registry names and `get_encoder(name, in_channels=3, depth=5, weights=None, output_stride=32, **kwargs)` to instantiate the encoder directly.
- For model constructors, pass the same backbone as `encoder_name=...` and weights as `encoder_weights=...`; see `../model-building/SKILL.md` for complete model recipes.
- For preprocessing, call `get_preprocessing_params(encoder_name, pretrained="imagenet")` when you need mean/std/input range as data, or `get_preprocessing_fn(encoder_name, pretrained="imagenet")` when you need a NumPy preprocessing callable.
- For timm universal encoders, prefer the `tu-` prefix. The pretrained variant belongs in the encoder name, and `encoder_weights` / `weights` should be `True` to request pretrained timm weights or `None` for random/offline initialization.
- For DPT, use `tu-` ViT-like encoder names supported by the DPT architecture and route full model construction details to `../model-building/SKILL.md`.

## Decision Flow

1. Choose a family from [encoder-reference.md](references/encoder-reference.md): native registry for stable ImageNet-style names, `tu-` timm universal for broad timm coverage, or DPT-compatible `tu-` ViT-style names for `smp.DPT`.
2. Decide whether weights may download. Use `weights=None` / `encoder_weights=None` for offline random initialization; use a native string such as `"imagenet"` only when downloads or cached configs are acceptable.
3. Align preprocessing with the weights choice. Preprocessing metadata is meaningful for pretrained weights; if the run is offline, collect params from cached/local config or hard-code a known policy deliberately.
4. Set `depth` and `output_stride` only when the model architecture expects them. Native encoders commonly produce `depth + 1` feature maps including the input; timm universal supports depth up to 5 and may reject unsupported output strides.
5. Validate an encoder choice with the bundled script before writing larger model code:

```bash
python sub-skills/encoders-preprocessing/scripts/check_encoder.py resnet34 --preprocessing-only
python sub-skills/encoders-preprocessing/scripts/check_encoder.py tu-resnet18 --weights none --depth 5
```

## References

- [Encoder reference](references/encoder-reference.md): native families, `tu-` naming, `timm-` migration, DPT caveats, depth, and output stride.
- [Preprocessing](references/preprocessing.md): `get_preprocessing_params`, `get_preprocessing_fn`, offline behavior, and data-shape caveats.
- [Troubleshooting](references/troubleshooting.md): wrong encoder names, wrong weights, Hugging Face/timm downloads, DPT fixed-size inputs, and unavailable preprocessing params.
- [check_encoder.py](scripts/check_encoder.py): inspect encoder/preprocessing metadata as JSON while avoiding downloads by default.

## Boundaries

- Model constructor recipes, decoder-specific parameters, and architecture selection belong in `../model-building/SKILL.md`.
- Losses, metrics, training loops, and evaluation belong in `../training-evaluation/SKILL.md`.
- Export, tracing, deployment, and runtime packaging belong in `../model-export/SKILL.md`.
