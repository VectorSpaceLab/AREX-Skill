---
name: retrieval-optimization
description: "Operate LimiX sample-retrieval ensemble inference and Optuna
  search-space tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Retrieval optimization

Use this sub-skill when you need to explain, preview, or tune the sample-retrieval ensemble path for a local LimiX checkpoint.

## What this covers
- sample-retrieval ensemble inference
- Optuna tuning over retrieval parameters
- attention-map generation for retrieval
- safe preview of the retrieval search space

## Route away
- Base predictor inputs, tensor shapes, and task-level inference: `../predictor-inference/SKILL.md`
- JSON schema, config generation, and config validation: `../configuration-preprocessing/SKILL.md`
- Benchmark CLI loops and `search_space_sample_num`: `../benchmark-cli/SKILL.md`

## Before you start
- Use a local LimiX checkpoint and a retrieval-enabled config list.
- Retrieval runs are CUDA/GPU-oriented; the shipped project notes that sample-retrieval ensemble inference is intended for very high-memory GPUs.
- Full checkpoint inference is not run here; use the bundled preview script first.

## Read first
- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/preview_retrieval_search_space.py`

## Safety rules
- Do not run Optuna tuning blindly at the default trial count on a large dataset.
- Do not pass a CPU device with `use_retrieval: true`.
- Do not assume the constructor's `attention_score` argument overrides the predictor's internal attention flow; the current search loop recomputes through the predictor path.

## Quick decision
- Need to inspect or validate ranges without running inference? Use `scripts/preview_retrieval_search_space.py`.
- Need to tune parameters for a local checkpoint? Follow `references/workflows.md`.
- Need to understand exact keys or signatures? Follow `references/api-reference.md`.
- Need a fix for OOM, missing attention, or config mismatch? Follow `references/troubleshooting.md`.
