---
name: vits
description: "Routes VITS text-to-speech workflows for data preparation,
  training, synthesis, and voice conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# VITS

Use this skill for the VITS repository when the task is about text-to-speech data preparation, single- or multi-speaker training, inference, or voice conversion.

## Start here

- Read `references/repo-provenance.md` if you want to check whether this skill still matches the current checkout.
- Read `references/workflows.md` for the end-to-end workflow map and the bundled helper scripts.
- Read `references/configuration.md` for the LJ Speech and VCTK config variants, filelist layouts, and key hyperparameters.
- Read `references/api-reference.md` when you need verified class, function, or method signatures.
- Read `references/troubleshooting.md` when an import, backend, data-format, or runtime step fails.

## Required setup

- Use a Python environment with the package dependencies installed.
- Install or verify the speech-text dependencies used by this repo: PyTorch with CUDA support for training and GPU inference, `librosa`, `phonemizer`, `Unidecode`, `scipy`, `tensorboard`, and `Cython`.
- Provide `espeak` or `espeak-ng` if you need `english_cleaners` or `english_cleaners2`.
- Build the monotonic-alignment extension before importing `models` or running any model smoke checks.

## Root routes

### `data-preparation`
Use this route for custom dataset preprocessing, filelist cleaning, dataset layout checks, `espeak`/phonemizer issues, and the monotonic-alignment build helper.

### `training`
Use this route for LJ Speech or VCTK training, checkpoint resume, DDP launch planning, config selection, and training diagnostics.

### `inference`
Use this route for text-to-speech synthesis, checkpoint-driven sample generation, and voice conversion.

## Shared helper scripts

- `scripts/check_install.py` — run this first to confirm the repo imports, CUDA is visible, and optional speech dependencies are present.
- `scripts/build_monotonic_align.py` — build the extension into the importable nested package layout expected by `monotonic_align`.
- `scripts/model_smoke.py` — run a tiny GPU forward, inference, or voice-conversion smoke check with synthetic tensors.
- `scripts/preprocess_text.py` — clean filelists for custom datasets.
- `scripts/launch_training.py` — print or launch the correct single- or multi-speaker training command with a safe `MASTER_PORT`.
- `scripts/synthesize.py` — synthesize speech or run voice conversion from a checkpoint and input text or audio.

## Using the routes

- Start with `data-preparation` if the problem is about filelists, text cleaners, or preparing custom corpora.
- Start with `training` if the problem is about configs, distributed launch, resume logic, or losses.
- Start with `inference` if the problem is about checkpoints, sample generation, or voice conversion outputs.
- Use `scripts/model_smoke.py` before any longer run when you need a quick environment or model check.

## What this skill does not do

- It does not replace the original repository checkout with generated content.
- It does not rely on the original checkout remaining at a fixed path.
- It does not cover unrelated speech frameworks or generic audio packages unless they are needed to use VITS itself.
