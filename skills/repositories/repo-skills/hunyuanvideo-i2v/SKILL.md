---
name: "hunyuanvideo-i2v"
description: "Guides HunyuanVideo-I2V image-to-video inference, LoRA training,
  and latent-extraction workflows, including checkpoint setup, CUDA/flash-attn
  requirements, and the safe bundled checks for this repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# HunyuanVideo-I2V

Use this skill for Tencent HunyuanVideo-I2V image-to-video workflows: single-GPU sampling, LoRA-based special-effects training, latent extraction for training data, checkpoint layout checks, and the repo-specific troubleshooting around CUDA, flash-attn, and DeepSpeed.

## Start Here

1. Read [`references/repo-provenance.md`](references/repo-provenance.md) if you need to confirm this skill matches the current checkout.
2. Read [`references/checkpoints.md`](references/checkpoints.md) before any real generation or training run.
3. Read [`references/model-overview.md`](references/model-overview.md) for supported model/config choices and the resolution/length constraints.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) when imports, CUDA, flash-attn, checkpoint, or data-layout checks fail.

## Install and Smoke Check

The checkout root is the directory containing `sample_image2video.py`, `train_image2video_lora.py`, `hyvideo/`, and `ckpts/`. The generated skill is stored separately under `skills/disco/hunyuanvideo-i2v`; it is not the checkout root. In the commands below, set `CHECKOUT_ROOT` to the real checkout and `SKILL_ROOT` to this skill directory, then run from `CHECKOUT_ROOT`:

```bash
export CHECKOUT_ROOT=<checkout-root>
export SKILL_ROOT="$CHECKOUT_ROOT/skills/disco/hunyuanvideo-i2v"
cd "$CHECKOUT_ROOT"
# decord 0.6.0 has limited pip wheels on newer Python versions; prefer conda-forge first.
conda install -c conda-forge decord=0.6.0
python -m pip install -r requirements.txt
```

`requirements.txt` is the fresh-install base: it pins `transformers==4.48.0` with compatible `tokenizers==0.21.0` and declares the direct HyVAE imports `decord==0.6.0` and `omegaconf==2.3.0`. On CPython versions without a matching decord wheel, install that dependency from conda-forge before running pip; do not silently substitute a fake package. PyTorch/CUDA wheels are intentionally not guessed here. Install a wheel matching the host separately; install `requirements-optional.txt` only for the matching GPU workflow (DeepSpeed, flash-attn, or xDiT).

The repository is CUDA-first. A lightweight import check that does not allocate CUDA is:

```bash
python "$SKILL_ROOT/scripts/check_runtime.py" --repo-root "$CHECKOUT_ROOT" --check-imports --check-decord --check-omegaconf
```

Add `--check-cuda --check-flash-attn --check-deepspeed` only after those optional backends are installed. Checkpoint validation is separate and does not download or invent weights:

```bash
python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode inference
```

If `pip check` or import smoke fails, read the troubleshooting reference before changing anything else.

## Choose a Route

### `inference`
Read [`sub-skills/inference/SKILL.md`](sub-skills/inference/SKILL.md) when the task is to generate a video from one image, compare stable vs dynamic motion, enable LoRA inference, or use xDiT sequence-parallel inference.

Typical signals:

- `sample_image2video.py`
- `--i2v-mode`
- `--i2v-image-path`
- `--i2v-resolution 360p|540p|720p`
- `--i2v-stability`
- `--use-lora`
- `--ulysses-degree` / `--ring-degree`
- `--use-cpu-offload`

### `lora-training`
Read [`sub-skills/lora-training/SKILL.md`](sub-skills/lora-training/SKILL.md) when the task is to train or resume a LoRA effect model, tune DeepSpeed settings, or inspect training-data expectations.

Typical signals:

- `train_image2video_lora.py`
- `--task-flag`
- `--output-dir`
- `--data-jsons-path`
- `--use-lora`
- `--lora-rank`
- `deepspeed --include localhost:0`

### `data-preparation`
Read [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md) when the task is to build VAE latents from raw videos, validate `meta_file.list` / raw caption JSON files, or inspect the processed latent JSON layout used by training.

Typical signals:

- `hyvideo/hyvae_extract/`
- `start.sh`
- `vae.yaml`
- `meta_file.list`
- raw `video_path` + `raw_caption.long caption`
- processed `json_path/*.json` + `.npy`

## Shared References and Scripts

- [`references/checkpoints.md`](references/checkpoints.md) — checkpoint tree, download commands, and missing-asset symptoms.
- [`references/model-overview.md`](references/model-overview.md) — model/config/resolution summary and output constraints.
- [`references/troubleshooting.md`](references/troubleshooting.md) — cross-cutting install, CUDA, flash-attn, checkpoint, and data-layout fixes.
- [`scripts/check_runtime.py`](scripts/check_runtime.py) — import and backend smoke checker.
- [`scripts/check_checkpoint_layout.py`](scripts/check_checkpoint_layout.py) — validates the expected `ckpts/` tree before you try to run a workflow.

## Notes

- Real inference and LoRA training both need the repo checkpoints in `ckpts/`; the repo does not ship them.
- `flash-attn` is required for the inspected runtime path because the model attention code uses it by default.
- The repository supports xDiT multi-GPU inference through `xfuser`, but that dependency is optional and not part of the minimum inspection environment.
