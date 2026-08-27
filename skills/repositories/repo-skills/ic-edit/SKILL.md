---
name: ic-edit
description: "Route ICEdit image-editing, Gradio demo, and LoRA training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ICEdit

Use this skill when the user wants to edit an image with ICEdit, launch the browser demo, or understand and prepare the shipped LoRA / MoE LoRA training paths.

## Route map

- `sub-skills/inference/SKILL.md` — one-shot CLI editing, seed control, 512-width normalization, CPU-offload guidance, and normal or MoE inference.
- `sub-skills/gradio/SKILL.md` — browser demo launch, share and port control, GGUF inputs, bundled presets, and UI troubleshooting.
- `sub-skills/training/SKILL.md` — config-driven LoRA and MoE LoRA training, dataset prep, launch-command construction, wandb, and checkpointing.

## Read first

- `references/repo-provenance.md` when you need the repository snapshot or want to check staleness.
- `references/installation.md` before preparing or reusing a Python environment.
- `scripts/check_icedit_env.py` to confirm CUDA and the installed import surface.
- `references/model-assets.md` for model ids, width rules, and bundled preset assets.
- `references/troubleshooting.md` for cross-cutting install, GPU, model, and download failures.
- `references/repo-routing-metadata.json` only when validating the managed
  area-family placement; it is not workflow guidance.

All commands below are cwd-independent when they use an absolute skill root. Set it once if convenient:

```bash
export ICEDIT_SKILL=/path/to/ic-edit-skill
```


## Operating notes

- ICEdit is GPU-first. The primary workflows expect a CUDA-capable torch build.
- The bundled helpers preserve the fixed diptych prompt template and the 512-pixel width rule from the repo scripts.
- Normal inference and normal Gradio are standalone helpers in this skill tree; their default Hub ids still download model weights.
- MoE inference/demo require an ICEdit checkout supplied with `--repo-root` (including its vendored `icedit/` package).
- Training requires a checkout's `train/src` and `train/train/config`; training source and configs are not bundled here.
- The training helper is dry-run by default; `--execute` is the explicit GPU/network action.

## Installation summary

1. Create or reuse a Python 3.11 environment with a CUDA-enabled torch wheel.
2. Install the base editing stack and the extra training support libraries listed in `references/installation.md`.
3. Run the environment checker with its rooted path, for example `python "$ICEDIT_SKILL/scripts/check_icedit_env.py"`.


## Fast intent routing

- Edit an image, change the seed, or honor the 512-width rule -> `inference`
- Open a browser UI, share a link, try GGUF, or adjust LoRA scale -> `gradio`
- Build or troubleshoot a training launch, config, or dataset path -> `training`

## Notes for future agents

- Read the provenance file before deciding whether this skill is stale for a new checkout.
- Keep runtime links inside this skill tree.
- Prefer the sub-skill that matches the user's immediate intent instead of a broader generic image-generation skill.
