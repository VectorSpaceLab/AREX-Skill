---
name: install-and-environment
description: "Install, inspect, and troubleshoot Megatron Core and Megatron-LM
  runtime environments."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# install-and-environment

Use this sub-skill when the task is about getting Megatron Core importable, choosing a Megatron-LM environment, checking CUDA readiness, or diagnosing dependency/build problems before training or inference.

## Read first

- For install modes, Python/CUDA/package variants, and optional dependency groups, read [references/install-reference.md](references/install-reference.md).
- For import failures, CPU-only Torch, CUDA/driver mismatch, build OOM, or optional TransformerEngine/Apex/ModelOpt warnings, read [references/troubleshooting.md](references/troubleshooting.md).
- To run a safe local probe, use [scripts/check_megatron_environment.py](scripts/check_megatron_environment.py). It checks package metadata, imports, optional modules, and CUDA availability without starting training.

## Quick route

| User asks about | Do this |
|---|---|
| "How do I install Megatron Core?" | Recommend PyPI or source install from [references/install-reference.md](references/install-reference.md), then run the bundled environment probe. |
| "Which extras do I need?" | Map the workflow: base import needs only `megatron-core`; training data/tokenizers need `[training]`; TE/ModelOpt/Mamba/FP8 paths require narrower optional extras or container-provided deps. |
| "CUDA is not available" | Check Torch wheel CUDA tag, driver max CUDA, device visibility, and container GPU passthrough; do not treat CPU import as GPU verification. |
| "TransformerEngine/Apex warnings appear" | Distinguish fallback-safe CPU/local paths from workflows that truly require TE/Apex/ModelOpt kernels. |
| "Editable install failed" | Check Python version, build dependencies, `MAX_JOBS`, and whether the user is trying to build broad dev extras outside the recommended container. |

## Minimal verification workflow

1. Identify whether the task is package use, repo development, or large-scale CUDA training.
2. Install the smallest dependency set that covers that task. Do not install all optional groups by default.
3. Run:

   ```bash
   python scripts/check_megatron_environment.py --check-cuda --optional transformer_engine apex modelopt mamba_ssm
   ```

   Run the bundled script from this skill directory or copy it into a scratch area. It prints JSON-like facts and exits nonzero only when explicitly required checks fail.
4. If the task will run real training/inference, continue to the owning sub-skill:
   - [../training-cli-and-data/SKILL.md](../training-cli-and-data/SKILL.md) for training/data/launches.
   - [../inference-and-serving/SKILL.md](../inference-and-serving/SKILL.md) for inference/server workflows.
   - [../core-models-and-parallelism/SKILL.md](../core-models-and-parallelism/SKILL.md) for model/parallelism API choices.

## Environment facts to preserve in answers

- Current Megatron-LM metadata packages the public distribution as `megatron-core` and imports as `megatron.core` / `megatron.training`.
- Current metadata requires Python `>=3.12` and base dependencies `torch>=2.6.0`, `numpy`, and `packaging`.
- The package is CUDA-centered. A CPU import check is useful, but it does not validate distributed training, NCCL, FP8, TransformerEngine kernels, or inference CUDA graphs.
- Broad development installs are heavy because optional packages may compile CUDA extensions. Prefer the NGC/container path for full dev, TE, ModelOpt, Mamba, FlashMLA, and DeepGEMM workflows.
- If build jobs exhaust memory, retry with a conservative `MAX_JOBS`, for example `MAX_JOBS=4`.

## Boundaries

- This sub-skill owns environment selection and import/backend diagnosis.
- Use [../training-cli-and-data/SKILL.md](../training-cli-and-data/SKILL.md) for command construction and data preprocessing.
- Use [../testing-ci-and-maintenance/SKILL.md](../testing-ci-and-maintenance/SKILL.md) for repo CI containers, `uv.lock`, lint groups, base image bump PRs, and golden-value workflows.
