---
name: big-sleep
description: "Routes Big Sleep text-to-image workflows, CUDA setup checks,
  prompt controls, and Python API usage for the `dream` CLI and `Imagine` API."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Big Sleep

Big Sleep turns a text prompt into an image by optimizing a BigGAN latent with CLIP guidance. Use this skill when a user wants to run `dream`, compose positive or negative prompts, save progress frames, tune generation settings, or diagnose the CUDA-only runtime.

## Start here

- Use `scripts/check_runtime.py --check-cli` to confirm the installed package, CUDA torch, and `dream --help`.
- Read `references/workflows.md` for end-to-end CLI and Python recipes.
- Read `references/api-reference.md` for verified signatures and method behavior.
- Read `references/troubleshooting.md` when import, CUDA, download, cache, or prompt-validation errors appear.
- Read `references/repo-provenance.md` to check whether this skill still matches the current repository snapshot.
- `references/repo-routing-metadata.json` feeds `repo-skills-router`; keep it aligned with this router.

## Install

Big Sleep is effectively CUDA-only because `big_sleep.big_sleep` asserts that CUDA is available during import.

Verified on this host:

```bash
python -m pip install --index-url https://download.pytorch.org/whl/cu124 torch torchvision
python -m pip install big-sleep
python -m pip check
dream --help
python scripts/check_runtime.py --check-cli
```

If your driver needs a different CUDA wheel tag, install a matching CUDA-enabled torch/torchvision pair instead of the example cu124 wheel.

## Main routes

- `dream` command-line runs → `references/workflows.md`
- `Imagine(...)` or `BigSleep(...)` from Python → `references/api-reference.md`
- Multi-prompt, negative prompt, save-best, save-progress, seeding, and file-naming questions → `references/workflows.md`
- Missing CUDA, missing `libcudnn`, stale torch wheels, or first-run downloads → `references/troubleshooting.md`
- Staleness / refresh decisions → `references/repo-provenance.md`

## Supported workflows

- Text-to-image generation from the `dream` CLI.
- Python generation with `Imagine`.
- Multi-prompt generation with `|`.
- Negative-prompt suppression with `text_min`.
- Image-conditioned runs with `img`.
- Save-best, save-progress, seeding, and filename controls.
- Low-level `BigSleep` control for custom loops.

## What this skill does not cover

- CPU-only execution.
- Diffusion, LoRA, or generic vision-model training stacks.
- Serving APIs or web apps.
- Repo-maintenance workflows.

## Notes

- The Fire CLI spells flags with underscores in the verified help output, such as `--save_progress`, `--save_best`, `--open_folder`, `--text_min`, `--max_classes`, and `--larger_model`; use explicit boolean assignments such as `--open_folder=False` for headless runs, not space-separated `--open_folder false`.
- The default `open_folder` behavior opens the output directory after a run starts; disable it on headless or remote sessions.
- Generated images are written to the current working directory unless you change where the command is invoked.
