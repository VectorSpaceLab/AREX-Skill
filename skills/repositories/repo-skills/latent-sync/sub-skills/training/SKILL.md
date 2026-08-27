---
name: training
description: "Configure and launch LatentSync U-Net and SyncNet training with
  safe config, file-list, DDP, checkpoint, and VRAM guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training

Route LatentSync training work through this sub-skill when the task involves choosing or adapting U-Net or SyncNet training configs, generating dataset file lists, rendering distributed launch commands, or diagnosing training-time config/checkpoint/VRAM failures.

## What this covers

- U-Net stage selection for `stage1`, `stage1_512`, `stage2`, `stage2_512`, and `stage2_efficient` configurations.
- SyncNet training selection for pixel, pixel-with-attention, and latent-space variants.
- Safe `torchrun` command rendering for `scripts.train_unet` and `scripts.train_syncnet` without executing long training unless explicitly requested.
- Dataset fileslist creation and preflight checks for training-ready `.mp4` clips.
- Checkpoint, DDP/NCCL, config-path, malformed-fileslist, and VRAM troubleshooting.

## Primary entry points

- [`scripts/run_training.py`](scripts/run_training.py) — render or explicitly execute a safe `torchrun` command for U-Net or SyncNet training; run it after editing a config copy and use `--preflight` to validate data/file-list paths.
- [`scripts/write_fileslist.py`](scripts/write_fileslist.py) — recursively write deterministic training fileslists from one or more processed dataset roots.
- [`references/workflows.md`](references/workflows.md) — U-Net and SyncNet training flow, dataset/file-list preparation, command patterns, and post-training validation notes.
- [`references/configuration.md`](references/configuration.md) — config anatomy and how the U-Net and SyncNet variants differ.
- [`references/troubleshooting.md`](references/troubleshooting.md) — failure-mode matrix for checkpoints, DDP, fileslists, VRAM, and config mismatches.

## Included source surfaces

- `scripts/train_unet.py` and `train_unet.sh`, adapted through `scripts/run_training.py`.
- `scripts/train_syncnet.py` and `train_syncnet.sh`, adapted through `scripts/run_training.py`.
- `tools/write_fileslist.py`, adapted as `scripts/write_fileslist.py`.
- `configs/unet/*.yaml`, `configs/syncnet/*.yaml`, `configs/audio.yaml`, and `configs/scheduler_config.json`, distilled in the bundled references and launcher metadata.
- `docs/syncnet_arch.md`, distilled in `references/configuration.md`.
- `latentsync/data/*_dataset.py`, `latentsync/models/*.py`, `latentsync/trepa/loss.py`, `latentsync/utils/util.py`, and `latentsync/whisper/audio2feature.py`, used to explain runtime requirements and failure modes.

## Explicitly excluded

- Raw preprocessing pipeline internals; use the data-preparation sub-skill for those stages.
- Inference UI/CLI operation; use the inference sub-skill after a checkpoint exists.
- Full metric/evaluation workflows; this sub-skill only notes the training scripts' built-in validation artifacts.

## Operational summary

- Run training from a LatentSync checkout because the repo has no packaging metadata; the bundled scripts accept `--repo-root` to make that explicit.
- Use `torchrun`, not direct `python -m`, because both training entry points initialize distributed state from torchrun-provided environment variables.
- Prefer the bundled launcher in dry-run mode first, then use `--execute` only after paths, fileslists, checkpoints, CUDA devices, and VRAM budget are verified.
- Treat `stage2_512.yaml` as a high-VRAM production configuration, not as a casual smoke target.
