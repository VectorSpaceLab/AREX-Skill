---
name: xingangpan-draggan
description: "Guides DragGAN and StyleGAN-Human workflows for interactive
  point-based GAN editing, pretrained StyleGAN generation, human-image
  manipulation, and SHHQ training setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DragGAN Repo Skill

Use this skill when a task involves DragGAN, “Drag Your GAN”, point-based GAN editing, StyleGAN2/3 checkpoint manipulation, the DragGAN desktop/Gradio visualizer, or the bundled StyleGAN-Human workflows.

This is a router. Read the smallest sub-skill that matches the user request, then use the linked references and bundled helpers from that sub-skill.

## First checks

1. Confirm the user has or will prepare a local DragGAN checkout or equivalent source tree when they want to run repo scripts. This skill does not bundle the full DragGAN source code or pretrained weights.
2. For runtime setup, read [references/installation-and-assets.md](references/installation-and-assets.md).
3. For environment diagnostics, run [scripts/check_environment.py](scripts/check_environment.py) with `--repo-root <DragGAN checkout>` when a checkout is available.
4. For checkpoint diagnostics shared by UI and generation, run [scripts/check_model_assets.py](scripts/check_model_assets.py) against the checkpoint directory.
5. To inspect the public checkpoint manifest without network access, run [scripts/download_draggan_checkpoints.py](scripts/download_draggan_checkpoints.py); add `--execute` only after reviewing the destination, URLs, license, and disk budget.
6. For source staleness, read [references/repo-provenance.md](references/repo-provenance.md).

## Route by task

| User request | Read next |
| --- | --- |
| Launch DragGAN, edit images by dragging points, use desktop GUI, use Gradio demo, debug masks/points/checkpoints in the visualizer | [sub-skills/draggan-ui/SKILL.md](sub-skills/draggan-ui/SKILL.md) |
| Generate images from StyleGAN2/3 pickles, convert legacy pickles, build generation/interpolation/style-mixing commands, reason about model filenames and seeds | [sub-skills/stylegan-generation/SKILL.md](sub-skills/stylegan-generation/SKILL.md) |
| StyleGAN-Human alignment, background whitening, real-image inversion with PTI, clothing-length attribute editing, InsetGAN, or missing human-model assets | [sub-skills/stylegan-human-manipulation/SKILL.md](sub-skills/stylegan-human-manipulation/SKILL.md) |
| Train StyleGAN-Human SG2/SG3 on SHHQ or plan GPU/dataset/output settings for training | [sub-skills/stylegan-training/SKILL.md](sub-skills/stylegan-training/SKILL.md) |
| Install/import/CUDA/OpenGL/Gradio/model-download problems not isolated to one workflow | [references/troubleshooting.md](references/troubleshooting.md) |

## Core runtime assumptions

- DragGAN editing is GPU-oriented. CUDA is required for truthful validation of interactive drag optimization in the original workflow; CPU can only cover imports and some parser checks.
- The top-level generation scripts can select CUDA, MPS, or CPU in PyTorch, but CPU generation is slow and not proof that the interactive editing path works.
- Most pretrained model files are external `.pkl` checkpoints. This skill provides preflight and command helpers, not model downloads by default.
- StyleGAN-Human alignment, PTI, editing, InsetGAN, and training require extra assets or large data that are intentionally preflighted before execution.
- Outputs preserve the project’s “AI Generated” watermark behavior in the renderer; do not remove it from derived workflows.

## Bundled root helpers

- [scripts/check_environment.py](scripts/check_environment.py) checks Python imports, optional repo imports, and CUDA visibility without starting a GUI or training run.
- [scripts/check_model_assets.py](scripts/check_model_assets.py) checks checkpoint directories and warns when DragGAN cannot infer a generator family from `.pkl` filenames.
- [scripts/download_draggan_checkpoints.py](scripts/download_draggan_checkpoints.py) lists the public checkpoint manifest and only downloads when `--execute` is explicit.

## Important constraints

- Do not run long training, large downloads, GUI servers, or optimization loops unless the user explicitly asks for execution and the required assets/hardware are present.
- Prefer dry-run command builders and asset preflight helpers before launching a heavy workflow.
- Do not route generic image-generation tasks here unless the task names DragGAN, StyleGAN2/3 pickles, StyleGAN-Human, point-based GAN editing, or matching repo-specific CLI/config errors.
