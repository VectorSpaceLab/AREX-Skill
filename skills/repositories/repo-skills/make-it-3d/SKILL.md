---
name: make-it-3d
description: "Use this repo skill for Make-It-3D single-image 3D creation,
  including CUDA asset setup, alpha-image validation, coarse NeRF optimization,
  refinement, rendering, export, and troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# Make-It-3D Repo Skill

Use this skill when a task is about operating Make-It-3D, the ICCV 2023 single-image-to-3D system that optimizes a NeRF with DPT depth, CLIP/Stable-Diffusion guidance, and a refinement/export stage. The skill is self-contained: use the bundled references and scripts here rather than reopening the source README, demos, or scripts just to recover commands, flags, dependencies, or failure handling.

Before giving run commands, check freshness in [references/repo-provenance.md](references/repo-provenance.md). The source snapshot is a script-style research repo, not a pip-installable root package. Future use normally starts from a Make-It-3D checkout plus a CUDA-capable Python environment.

## Route Map

| User need | Read next | Why |
| --- | --- | --- |
| Install/diagnose dependencies, DPT weights, Hugging Face access, alpha-mask inputs, or hardware readiness | [environment-and-inputs](sub-skills/environment-and-inputs/SKILL.md) | Owns CUDA/dependency planning, model assets, input PNG requirements, and reusable environment/input checks. |
| Build the two coarse-stage commands, tune camera ranges, select CLIP vs Stable Diffusion guidance, or debug geometry during training | [coarse-training](sub-skills/coarse-training/SKILL.md) | Owns front-view and 360-degree NeRF optimization, important `main.py` flags, outputs, and geometry failures. |
| Continue to refine stage, render videos, test checkpoints, save meshes, or reason about point-cloud/mesh export dependencies | [refinement-and-export](sub-skills/refinement-and-export/SKILL.md) | Owns refine/test/export command construction, generated output layout, and mesh/point-cloud troubleshooting. |
| Cross-cutting install/import, missing module, CUDA extension, credential, output, or quality issues | [references/troubleshooting.md](references/troubleshooting.md) | Summarizes failures that span multiple sub-skills. |

## Minimal Operating Sequence

1. **Confirm a compatible environment before long runs.** Use [scripts/make_it_3d_env_check.py](scripts/make_it_3d_env_check.py) against the user's working checkout and asset locations. Make-It-3D expects CUDA for the practical pipeline; the source forces `opt.cuda_ray = True`, so raymarching CUDA support matters even when a user asks for `--backbone vanilla`.
2. **Validate the reference image.** The main script reads `--ref_path` with `cv2.IMREAD_UNCHANGED` and immediately converts BGRA to RGBA, so the reference should be a four-channel image with a usable foreground alpha mask. Use [sub-skills/environment-and-inputs/scripts/validate_alpha_input.py](sub-skills/environment-and-inputs/scripts/validate_alpha_input.py).
3. **Avoid unnecessary BLIP2 downloads when possible.** If the user already knows the object prompt, pass `--text "..."`; otherwise `main.py` loads BLIP2 (`Salesforce/blip2-opt-2.7b`) for captioning, which requires network/model cache and substantial GPU memory.
4. **Run coarse optimization in two phases.** Use [sub-skills/coarse-training/scripts/build_training_commands.py](sub-skills/coarse-training/scripts/build_training_commands.py) to emit the README-backed frontal phase and full-360 phase with correct flags.
5. **Run refinement/export only after a usable coarse workspace exists.** Use [sub-skills/refinement-and-export/scripts/build_refine_export_commands.py](sub-skills/refinement-and-export/scripts/build_refine_export_commands.py). Note that in the inspected source the refine block is nested under the `--final` path; include `--final --refine` if `--refine` alone does not execute refinement.

## Public Install Skeleton

Use the exact versions required by the user's machine when possible, but the source documentation used this public install pattern:

```bash
pip install torch==1.10.0+cu113 torchvision==0.11.1+cu113 torchaudio==0.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html
pip install git+https://github.com/NVlabs/tiny-cuda-nn/#subdirectory=bindings/torch
pip install git+https://github.com/openai/CLIP.git
pip install git+https://github.com/huggingface/diffusers.git git+https://github.com/huggingface/huggingface_hub.git
pip install git+https://github.com/facebookresearch/pytorch3d.git
pip install git+https://github.com/S-aiueo32/contextual_loss_pytorch.git
pip install -r requirements.txt
pip install ./raymarching
```

Read [references/backend-and-assets.md](references/backend-and-assets.md) before executing this literally: the repository pins older CUDA/PyTorch-era dependencies, while modern hosts often require adjusted torch/PyTorch3D/tiny-cuda-nn builds.

## Do Not Do This

- Do not start training before checking CUDA, raymarching build/toolkit readiness, DPT weights, Hugging Face access/cache, and alpha input validity.
- Do not promise CPU reproduction of the main Make-It-3D pipeline. CPU checks can validate scripts and some source facts, but they do not substitute for CUDA training/rendering behavior.
- Do not tell future users to read the original README or source files for basic commands. The equivalent distilled guidance is in this skill tree.
- Do not expose local environment names, absolute checkout paths, or private tokens in user-facing outputs. Ask users to provide their own paths and credentials at runtime.
