---
name: kair
description: "Repo-specific operating skill for KAIR image/video restoration:
  training configs, image testing, VRT/RVRT video workflows, dataset
  preparation, model downloads, and environment checks."
metadata:
  disco-role: operating
  repo: cszn/KAIR
  source-commit: fc1732f4a4514e42ce15e5b3a1e18c828af47a1e
disable-model-invocation: true
license: MIT
---

# KAIR operating skill

Use this skill when a user asks for help operating the KAIR repository (`cszn/KAIR`) for image restoration, super-resolution, denoising, deblurring, face enhancement, SwinIR, VRT/RVRT, dataset preparation, model-zoo checkpoints, or KAIR option JSONs.

This is a repository-specific operating graph. Do not ask the user to inspect the original KAIR source for normal routing; use the bundled references and sub-skills first. When native execution is requested, assume the user has a KAIR checkout and run KAIR scripts from the checkout root.

## First route by task

| User task | Load this sub-skill/reference |
| --- | --- |
| Train an image model, edit/validate KAIR option JSON, choose `model`/`dataset_type`/`netG`, DDP launch, resume/fine-tune | `sub-skills/image-training/SKILL.md` |
| Run image denoising/SR/deblocking/deblurring/face-enhancement/challenge inference, choose checkpoints, build SwinIR/DnCNN commands | `sub-skills/image-testing/SKILL.md` |
| Run or train VRT/RVRT video SR, deblurring, denoising, frame interpolation, task IDs `001`-`009` or `001`-`006`, video tiling/OOM | `sub-skills/video-restoration/SKILL.md` |
| Prepare datasets, check trainsets/testsets layout, plan subimages, LMDBs, REDS/Vimeo/DVD/GoPro/DAVIS/UDM10/Set8 data | `sub-skills/data-preparation/SKILL.md` |
| Check Python/CUDA/toolchain readiness | `references/setup-and-environment.md` and `scripts/kair_check_environment.py` |
| Download or locate model-zoo checkpoints | `references/model-zoo-and-downloads.md` and `scripts/kair_download_models.py` |
| Diagnose cross-cutting failures | `references/troubleshooting.md` |

## Minimal setup preflight

KAIR is a source-script repo. From a KAIR checkout root, use an isolated Python environment and install public dependencies before native script execution:

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -r requirement.txt
python -m pip install ninja
python -m pip check
python skills/disco/kair/scripts/kair_check_environment.py --kair-root .
```

For VRT/RVRT or face-enhancement custom-op work, require CUDA-capable PyTorch plus a CUDA toolkit and run the custom-op preflight from `references/setup-and-environment.md` before claiming full backend readiness.

## Root references and scripts

Read these root references before giving broad KAIR setup or checkpoint advice:

- `references/repo-provenance.md` documents the source anchor, inspected evidence, included scope, and construction boundaries.
- `references/setup-and-environment.md` explains the source-script install pattern, backend requirements, CUDA/custom-op checks, and safe parser probes.
- `references/model-zoo-and-downloads.md` maps checkpoint groups, destination conventions, URL families, and auto-download caveats.
- `references/troubleshooting.md` is the cross-skill troubleshooting index.
- `references/repo-routing-metadata.json` contains router-facing scenario tags and entry-point ownership.

Bundled helper scripts are dry-run or read-only by default:

- `scripts/kair_check_environment.py` checks imports, PyTorch CUDA, optional KAIR source imports, and optional custom-op imports.
- `scripts/kair_download_models.py` prints checkpoint URL/destination plans by default and downloads only with `--execute`.

## Backend gate

Treat backend verification as task-specific:

- CPU-only is acceptable for reading/editing option JSONs, building commands, and checking dataset layouts.
- Full image inference/training usually needs a realistic CUDA budget, even if some scripts can run on CPU.
- VRT/RVRT and face-enhancement custom-op workflows are CUDA-first and are only partially verified without CUDA.
- RVRT/custom-op checks require a CUDA-capable PyTorch build, `nvcc`, and `ninja`.
- MATLAB scripts are reference-only unless the user explicitly provides a MATLAB runtime and asks to run them.

If a user asks for auto-import or publication, do not import this skill unless final verification has passed and backend gates match the intended use. The production request for this graph explicitly disabled import.

## Safe operating rules

1. Prefer bundled dry-run helpers before launching native KAIR scripts.
2. Confirm checkpoint and dataset paths before running scripts that can download assets or process large folders.
3. For training, validate a copied option JSON and ensure `task`, `path.root`, `gpu_ids`, `--nproc_per_node`, dataset roots, `model`, `dataset_type`, and `netG.net_type` are aligned.
4. For VRT/RVRT, choose the exact task ID first, then folder roots, checkpoint path, tile/overlap, `--sigma` if denoising, and whether metrics are possible.
5. For data preparation, inspect layout and disk budget first; several original KAIR helper scripts are destructive or write large outputs.
6. Preserve partial training checkpoints and partial downloads on transient failures unless the user explicitly asks to clean them.
7. Do not expose private construction environment paths in user-facing commands; use portable environment variables and user-provided paths.

## Verification status

The skill was generated from live source inspection and private environment probes. It intentionally did not run full KAIR training, full inference, destructive data preparation, or MATLAB evaluation during construction. Final publication/auto-import requires the verification artifacts under `skills/tests/kair/` to pass.
