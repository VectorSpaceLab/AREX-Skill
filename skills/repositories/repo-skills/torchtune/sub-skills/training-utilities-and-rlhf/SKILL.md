---
name: training-utilities-and-rlhf
description: "Use torchtune training utilities, checkpointers, precision,
  memory/distributed helpers, logging/profiling, schedulers, and RLHF/GRPO
  utilities safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# training-utilities-and-rlhf

Use this sub-skill when a torchtune task is about checkpoint format/resume mechanics, precision or dtype choices, memory and distributed utility behavior, metric logging, profiling, LR schedulers, RLHF sequence/reward utilities, or the experimental GRPO/async RL boundaries.

## Route Here For

- Choosing or debugging `FullModelHFCheckpointer`, `FullModelMetaCheckpointer`, `FullModelTorchTuneCheckpointer`, `DistributedCheckpointer`, resume state, or async checkpointing.
- Explaining `get_dtype`, `set_seed`, distributed backend selection, activation checkpointing/offloading, optimizer-in-backward, memory stats, profiler config, or cosine warmup scheduling.
- Selecting metric loggers such as `DiskLogger`, `StdoutLogger`, `WandBLogger`, `CometLogger`, `TensorBoardLogger`, or `MLFlowLogger` and their optional dependency implications.
- Using public `torchtune.rlhf` sequence/log-prob/reward helpers for PPO/DPO/GRPO-style pipelines.
- Treating `torchtune.dev.grpo` and `torchtune.dev.rl` as experimental code with extra Ray/vLLM/async RL requirements.

## Safe Workflow

1. Run the bundled runtime preflight before planning distributed or RL jobs: `python scripts/check_training_runtime.py`.
2. Match checkpoint component to source format first, then align `checkpoint_dir`, `checkpoint_files`, `model_type`, `output_dir`, and resume flags.
3. Check dtype/device support with `get_dtype(dtype, device)` semantics before assuming `bf16` or optional quantization paths work.
4. For distributed runs, choose recipe/launch shape in [post-training-recipes](../post-training-recipes/SKILL.md), then use this sub-skill for backend, rank/env, and checkpoint utility behavior.
5. For RLHF internals, prefer public `torchtune.rlhf` utilities and config-referenced losses; do not depend on unstable `torchtune.dev` APIs unless the user explicitly accepts experimental constraints.

## Read Next

- [Checkpointing and training utilities](references/checkpointing-and-training-utils.md) for checkpointer constructors, precision, memory, distributed, schedulers, logging, and profiling details.
- [RLHF and GRPO](references/rlhf-and-grpo.md) for public RLHF utility signatures, DPO/PPO loss caveats, and experimental GRPO/async RL boundaries.
- [Troubleshooting](references/troubleshooting.md) for checkpoint mismatches, resume/async failures, dtype/device errors, optional logger deps, profiler output, RLHF import issues, and async RL constraints.
- [post-training-recipes](../post-training-recipes/SKILL.md) for selecting and adapting recipe/config names without importing recipes.
- [data-and-datasets](../data-and-datasets/SKILL.md) for DPO/preference dataset row schemas.
- [inference-evaluation-quantization](../inference-evaluation-quantization/SKILL.md) when a trained checkpoint becomes an inference, evaluation, or quantization input.

## Bundled Helper

- `scripts/check_training_runtime.py` reports Python, torch, CUDA/MPS/XPU availability, `torchao` import health, torchtune training/RLHF import health, the current `torchtune.rlhf.loss` status, and optional async RL packages. It does not initialize distributed process groups, load checkpoints, start Ray/vLLM, or run training.

## Guardrails

- Do not `import recipes`; use `tune run`, `tune cp`, `tune cat`, `tune validate`, registry names, or CLI/runpy behavior through sibling skills.
- Do not launch distributed training, Ray, vLLM, W&B, Comet, or checkpoint downloads as a diagnostic without explicit user approval.
- Do not assume `torchtune.dev` APIs are stable; they are experimental and may change without compatibility guarantees.
- Do not leak local machine paths, tokens, environment names, or review artifact paths into reusable configs or public skill content.
