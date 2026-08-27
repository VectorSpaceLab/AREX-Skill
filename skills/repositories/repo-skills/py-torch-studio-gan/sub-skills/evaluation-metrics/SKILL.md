---
name: evaluation-metrics
description: "Evaluate StudioGAN image folders with IS/FID/PRDC, cache feature
  and moment inputs, choose backbones/resizers, and troubleshoot metric
  backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StudioGAN evaluation metrics

Use this sub-skill when a task asks to evaluate generated or real image folders with StudioGAN metrics, choose an evaluation backbone or post-resizer, reuse precomputed reference features/moments, or diagnose metric input, CUDA, DDP, pretrained-weight, or cache failures.

## First decision

- If the user has image folders to compare, use StudioGAN's standalone image-folder evaluator and read [the CLI reference](references/evaluate-cli-reference.md).
- If the user is configuring training-time `-metrics`, iFID, or CAS behavior from `python src/main.py`, read [the metrics overview](references/evaluation-metrics.md), then route config/dataset edits to [training and configuration](../training-and-configuration/SKILL.md) and checkpoint analysis execution to [sampling and analysis](../sampling-and-analysis/SKILL.md).
- If the user asks about `InceptionV3_tf`, `InceptionV3_torch`, `ResNet50_torch`, `SwAV_torch`, `DINO_torch`, `Swin-T_torch`, `legacy`, `clean`, `friendly`, or cached `.npz` files, read [backbones, resizers, and caches](references/backbones-resizers-and-caches.md).
- For errors, read [troubleshooting](references/troubleshooting.md) before retrying a long metric run.

## Safe helper scripts

The bundled scripts do not execute StudioGAN metrics, do not download weights, and do not train. They require explicit paths supplied by the caller.

- Build a dry-run command:

  ```bash
  python scripts/evaluate_image_folders_command.py \
    --repo-root /path/to/PyTorch-StudioGAN \
    --dset1 /path/to/real_imagefolder \
    --dset2 /path/to/generated_imagefolder \
    --metrics fid prdc \
    --gpus 0
  ```

- Check input combinations and lightweight folder/cache structure:

  ```bash
  python scripts/check_metric_inputs.py \
    --dset1 /path/to/real_imagefolder \
    --dset2 /path/to/generated_imagefolder \
    --metrics fid prdc
  ```

## Non-negotiable routing and safety notes

- Do not claim meaningful metric values from CLI help, config compatibility, tiny fixtures, or command-builder checks. Those only prove wiring and argument compatibility.
- The actual StudioGAN evaluation path is GPU-oriented: it queries `torch.cuda.current_device()` and moves models/tensors to CUDA devices. Treat CPU-only metric execution as unsupported unless the user has patched the checkout.
- Standalone folder metrics expect ImageFolder-like directories with class subdirectories, even for generated samples.
- `--dset1_feats` and `--dset1_moments` are different cache files. FID needs a real/reference folder or moments; PRDC needs a real/reference folder or features.
- Legacy TensorFlow 1.x inception-score code is not part of the current verified PyTorch metric path.
