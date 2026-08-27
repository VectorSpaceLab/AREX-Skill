---
name: stylegan-generation
description: "Guides DragGAN and StyleGAN-Human batch generation, interpolation,
  style mixing, video command planning, and legacy pickle conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StyleGAN Generation

Use this route for non-interactive generation from StyleGAN2/3 pickles, StyleGAN-Human generation, latent interpolation, style-mixing grids/videos, seed/truncation planning, or legacy pickle conversion.

## Command planning

Use the bundled command builder; it prints commands and never runs model inference:

```bash
python sub-skills/stylegan-generation/scripts/build_generation_command.py \
  --repo-root /path/to/DragGAN gen-images \
  --network checkpoints/model.pkl --seeds 1,2,5-10 --outdir outputs/generated
```

Read [references/generation-workflows.md](references/generation-workflows.md) for each workflow and [references/model-loading-and-conversion.md](references/model-loading-and-conversion.md) for checkpoint formats and naming. Use [references/troubleshooting.md](references/troubleshooting.md) before retrying a failed command.

## Main routes

- Top-level generation: seed ranges, truncation, noise mode, conditional class labels, translation, rotation, and output image names.
- StyleGAN-Human generation: choose version 1/2/3 explicitly; v2/v3 use the PyTorch path, while v1 needs a TensorFlow 1.x-compatible environment.
- Interpolation: exactly two useful seeds, GIF frame count, FPS, and optional intermediate frames.
- Style mixing: row/column seed grids and style-layer ranges.
- Style-mixing video: expensive and import-gated by the source’s TensorFlow `dnnlib.tflib` import; use only after checking that dependency.
- Legacy conversion: convert supported TensorFlow-era StyleGAN2/StyleGAN2-ADA pickles into the native PyTorch pickle format.

## Related routes

- Interactive point editing: [../draggan-ui/SKILL.md](../draggan-ui/SKILL.md).
- StyleGAN-Human alignment, PTI, attribute editing, and InsetGAN: [../stylegan-human-manipulation/SKILL.md](../stylegan-human-manipulation/SKILL.md).
- Training: [../stylegan-training/SKILL.md](../stylegan-training/SKILL.md).

## Bundled files

- [scripts/build_generation_command.py](scripts/build_generation_command.py) builds exact option names without executing.
- [references/generation-workflows.md](references/generation-workflows.md) contains task recipes and output expectations.
- [references/model-loading-and-conversion.md](references/model-loading-and-conversion.md) contains model and conversion rules.
- [references/troubleshooting.md](references/troubleshooting.md) contains generation-specific recovery.
