---
name: core-models
description: "Use this repo skill for Swin Transformer model construction,
  architecture inspection, tensor-shape checks, and CPU model smoke tests across
  Swin V1, Swin V2, Swin-MLP, and SimMIM encoder variants."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# core-models

Use this sub-skill when the task is about the model classes themselves: which constructor to use, how `build_model` dispatches on `MODEL.TYPE`, which config fields control architecture shape, how window partitioning works, or how to run a small CPU smoke check without touching the training loops.

## What this sub-skill covers

- `build_model(config, is_pretrain=False)` dispatch for `swin`, `swinv2`, `swin_moe`, and `swin_mlp`.
- `SwinTransformer`, `SwinTransformerV2`, and `SwinMLP` signatures and the config fields they read.
- SimMIM encoder construction through `models/simmim.py` when the question is about the encoder object or a tiny reconstruction smoke.
- Window helper behavior: partition/reverse shapes, shifted windows, and why image size and window size must be compatible.
- CPU-only sanity checks: instantiate a small model, count parameters, and run a minimal forward pass.

## What it does not cover

- ImageNet folder/zip/22K data-layout problems: use `data-and-checkpoints`.
- Training, fine-tuning, evaluation, throughput, DDP, or AMP command composition: use `training-eval-cli`.
- SimMIM end-to-end scripts and checkpoint remapping details: use `simmim-workflows`.
- MoE/Tutel/Apex/fused CUDA questions: use `moe-and-acceleration`.

## Typical user triggers

- "Which config should I use for SwinV2-Tiny?"
- "What does `MODEL.TYPE` need for Swin-MLP?"
- "Why does my image/window size break the model constructor?"
- "How can I build a tiny CPU smoke test for `build_model`?"
- "What is the difference between Swin V1 and Swin V2 position bias behavior?"

## Core workflow

1. Read the config family map in `references/model-construction.md`.
2. Confirm the model family from `MODEL.TYPE` and the config file path.
3. Check the relevant constructor signature in `references/api-reference.md`.
4. If the request is about safe inspection, run `scripts/smoke_model_build.py` with a repo checkout and a small config override.
5. If the request is about a constructor error, read `references/troubleshooting.md` for the shape mismatch or optional-backend warning.

## Safe checks

- Building a tiny CPU model is safe when `DATA.IMG_SIZE`, `MODEL.*.WINDOW_SIZE`, and the stage depths are reduced consistently.
- The helper script does not download weights or start distributed training.
- Optional fused window-process warnings are expected when the CUDA extension is missing; they are not baseline failures.

## Related references and scripts

- Read `references/api-reference.md` for verified signatures and the key architecture fields.
- Read `references/model-construction.md` when choosing a config family or reducing a config for smoke tests.
- Read `references/troubleshooting.md` for common constructor and shape errors.
- Run `scripts/smoke_model_build.py` when you want a tiny CPU construction check.
