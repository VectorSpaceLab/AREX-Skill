---
name: training
summary: "Configure and troubleshoot rLLM RL/SFT training backends and
  gateway-backed rollouts."
description: "Use rLLM training APIs and CLI for AgentTrainer, AgentSFTTrainer,
  Tinker/Verl/Fireworks backends, RL algorithms, SFT data/config, remote
  runtimes, and model-gateway trace capture."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# rLLM Training

Use this sub-skill when the task mentions `rllm train`, `rllm sft`, `AgentTrainer`, `AgentSFTTrainer`, `BackendProtocol`, `TinkerBackend`, `VerlBackend`, `FireworksBackend`, `SFTSpec`, rollout engines, GRPO/PPO/REINFORCE++/DAPO/CISPO, `async_training`, `remote_runtime`, gateway traces, LoRA rank, checkpointing, or backend validation errors.

## Start Here

1. Read `references/backend-matrix.md` before selecting or installing a backend. Tinker/Fireworks are service-backed; Verl is local distributed and GPU-heavy.
2. Read `references/training-workflows.md` for `rllm train`, `rllm sft`, and programmatic `AgentTrainer`/`AgentSFTTrainer` patterns.
3. Read `references/trainer-api.md` for current import locations, constructor signatures, algorithm config notes, and SFT spec fields.
4. Read `references/sft-data-and-config.md` when SFT files, message rows, eval-to-SFT curation, or tokenization methods are involved.
5. Read `references/troubleshooting.md` for backend validation errors, gateway trace issues, and required-backend limitations.
6. Use `../evaluation/SKILL.md` for AgentFlow/Evaluator implementation and `../datasets/SKILL.md` for benchmark/data layout.

## Safe Checks

```bash
python scripts/check_training_backends.py
python scripts/dump_train_config.py --model-name Qwen/Qwen3-8B --group-size 2 --batch-size 4
```

`check_training_backends.py` reports optional dependency and CUDA visibility. `dump_train_config.py` prints the config produced by the train CLI merger. Neither helper launches training. Missing optional backends are not failures unless the user's selected workflow requires them.

## Verification Caveat

CPU/import checks can validate this skill's guidance and config shape, but cannot prove local Verl training, Tinker service training, Fireworks service training, remote AgentCore execution, or long RL/SFT runs. Preserve those as required-backend verification items unless the user explicitly narrows scope.
