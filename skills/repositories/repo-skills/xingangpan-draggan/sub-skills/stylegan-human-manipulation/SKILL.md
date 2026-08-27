---
name: stylegan-human-manipulation
description: "Guides StyleGAN-Human alignment, background preprocessing, PTI
  inversion, latent-direction editing, real-image workflows, InsetGAN, and asset
  preflight."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StyleGAN-Human Manipulation

Use this route for human-image preparation and editing rather than basic generation: whitening backgrounds, aligning raw photos, inverting real images with PTI, applying `upper_length`/`bottom_length` edits, or composing face/body images with InsetGAN.

## Asset-first workflow

Run the preflight helper before touching model code:

```bash
python sub-skills/stylegan-human-manipulation/scripts/check_stylegan_human_assets.py \
  --repo-root /path/to/DragGAN \
  --check-alignment --check-pti --check-editing --check-insetgan
```

Missing assets are expected in a fresh checkout. Do not replace a missing model, latent direction, or segmentation file with a random download.

## Choose a route

- CPU-safe foreground/background processing: [references/alignment-and-data-prep.md](references/alignment-and-data-prep.md) and the bundled `bg_white.py`.
- Raw human photo to aligned 512x1024 image: alignment prerequisites and the one-person constraint in the same reference.
- Real image to editable latent: PTI configuration and outputs in [references/inversion-and-editing.md](references/inversion-and-editing.md).
- Generated or PTI-edited human image: attribute editing with `upper_length` or `bottom_length`.
- Face/body fusion: InsetGAN, which needs separate face/body checkpoints and dlib models.

## Background whitening

The bundled helper is self-contained and CPU-safe:

```bash
python sub-skills/stylegan-human-manipulation/scripts/bg_white.py \
  --raw-img-dir raw_images --raw-seg-dir masks --outdir white_background
```

It requires matching filenames and writes one output per valid raw/mask pair. Use a tiny fixture first; the helper returns non-zero when no pair can be processed.

## Real-image route

For real-image editing, keep the order explicit: raw image -> alignment -> PTI/e4e inversion -> attribute edit. PTI path and global settings are file-based in the source workflow, so use the reference checklist and preflight helper before launching a long CUDA optimization.

## Related routes

- Basic generation, interpolation, and style mixing: [../stylegan-generation/SKILL.md](../stylegan-generation/SKILL.md).
- Interactive DragGAN point editing: [../draggan-ui/SKILL.md](../draggan-ui/SKILL.md).
- SHHQ/StyleGAN2/3 training: [../stylegan-training/SKILL.md](../stylegan-training/SKILL.md).

## Bundled files

- [scripts/check_stylegan_human_assets.py](scripts/check_stylegan_human_assets.py) checks expected assets without downloading.
- [scripts/bg_white.py](scripts/bg_white.py) adapts the deterministic background-whitening utility.
- [references/alignment-and-data-prep.md](references/alignment-and-data-prep.md) covers image/mask layouts and alignment prerequisites.
- [references/inversion-and-editing.md](references/inversion-and-editing.md) covers PTI, edit, InsetGAN, and configuration.
- [references/troubleshooting.md](references/troubleshooting.md) covers optional dependencies and failure recovery.
