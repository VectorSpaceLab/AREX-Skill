---
name: areal
description: "Use AReaL for large-scale asynchronous LLM reinforcement learning,
  agentic RL, distributed post-training, inference/agent services, backend
  planning, and customization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AReaL Repo Skill

AReaL is a Python framework for asynchronous reinforcement learning and post-training of LLM, VLM, and agentic systems. Use this skill when a task asks how to configure, run, customize, or debug AReaL experiments, services, datasets, rewards, workflows, or distributed backends.

This generated skill is self-contained operating guidance. Do not depend on the original checkout being present; use the bundled references and scripts here.

## First questions to answer

1. **Workflow type**: config-driven post-training, custom dataset/reward/workflow, backend/distributed debugging, or v2 service operation?
2. **Runtime variant**: SGLang CUDA, vLLM CUDA, training-only CUDA, CPU/import-only inspection, sandbox, or vendor accelerator branch?
3. **Resource shape**: local/Ray/Slurm, nodes, GPUs per node, shared storage, model path, and whether rollout and training roles are separated or colocated?
4. **Safety**: is this only a command/config review, or may the agent start services, run training, download data/models, or use credentials?

## Install and import baseline

AReaL supports Python `>=3.11,<3.13`. For real training and inference, prefer the project runtime image or a `uv` environment matching the intended backend variant.

Common install choices:

```bash
# Default CUDA runtime: training packages plus SGLang inference.
uv sync --extra cuda

# vLLM variant: use the vLLM project manifests before syncing.
cp pyproject.vllm.toml pyproject.toml
cp uv.vllm.lock uv.lock
uv sync --extra cuda

# CPU/import-oriented development only; not proof of backend runtime.
uv sync
```

Minimal import smoke after installation:

```bash
python - <<'PY'
import areal
from areal.api.cli_args import GRPOConfig, SFTConfig
print(areal.__version__)
print(GRPOConfig.__name__, SFTConfig.__name__)
PY
```

For a safe environment and CLI check that does not launch training or services, run [`scripts/areal_env_doctor.py`](scripts/areal_env_doctor.py).

## Route by task

| User task | Read next |
|---|---|
| Run or adapt GRPO/PPO/SFT/DPO/RW experiments, choose trainer/config class, validate YAML and overrides, checkpoint/logging/recovery | [`sub-skills/post-training-experiments/SKILL.md`](sub-skills/post-training-experiments/SKILL.md) |
| Add or debug datasets, reward functions, `RLVRWorkflow`, `VisionRLVRWorkflow`, multi-turn/tool workflows, or agent framework integrations | [`sub-skills/custom-data-rewards-workflows/SKILL.md`](sub-skills/custom-data-rewards-workflows/SKILL.md) |
| Choose FSDP/Megatron/Archon/SGLang/vLLM backends, parse backend strings, plan GPU allocation, debug CUDA/NCCL/OOM/LoRA/FP8/weight sync | [`sub-skills/distributed-engines-backends/SKILL.md`](sub-skills/distributed-engines-backends/SKILL.md) |
| Operate `areal inf`, `areal agent`, `areal train`, model registration, service state/logs/status, online RL sessions, Hermes-style loops | [`sub-skills/services-cli-operations/SKILL.md`](sub-skills/services-cli-operations/SKILL.md) |

## Shared references

- [`references/package-overview.md`](references/package-overview.md): AReaL architecture, package layout, public entry points, and installed-package facts.
- [`references/configuration-cheatsheet.md`](references/configuration-cheatsheet.md): shared config classes, override syntax, backend fields, and cross-skill config rules.
- [`references/troubleshooting.md`](references/troubleshooting.md): cross-cutting install/import, backend variant, config, GPU, service, checkpoint, and credential failure modes.
- [`references/repo-provenance.md`](references/repo-provenance.md): source snapshot and evidence baseline for refresh decisions.

## Operating defaults

- Prefer **single-controller mode** for new experiments: a Python driver loads a config, creates trainers/controllers, and uses `scheduler.type=local|ray|slurm`.
- Treat legacy SPMD launchers as compatibility paths. Do not introduce them unless the user explicitly asks for the old mode.
- Prefer **proxy-style agent workflows** for new agentic RL integrations. Use direct `ArealOpenAI` only for legacy/framework-specific cases.
- Treat CUDA, SGLang, vLLM, Megatron, Archon, Ray, Slurm, sandbox, and NPU capabilities as backend-specific. A CPU import check does not prove them.
- Never run long training, start services, download model/data artifacts, mutate CUDA/driver stacks, or use credentials without explicit user approval.

## Safe bundled scripts

- [`scripts/areal_env_doctor.py`](scripts/areal_env_doctor.py): import/CLI/backend visibility check.
- [`sub-skills/post-training-experiments/scripts/validate_experiment_config.py`](sub-skills/post-training-experiments/scripts/validate_experiment_config.py): safe config/override validator.
- [`sub-skills/custom-data-rewards-workflows/scripts/check_workflow_contract.py`](sub-skills/custom-data-rewards-workflows/scripts/check_workflow_contract.py): dataset/reward/workflow import and sample-contract checker.
- [`sub-skills/distributed-engines-backends/scripts/check_backend_plan.py`](sub-skills/distributed-engines-backends/scripts/check_backend_plan.py): backend-string and GPU-demand checker.
- [`sub-skills/services-cli-operations/scripts/check_service_cli.py`](sub-skills/services-cli-operations/scripts/check_service_cli.py): static service CLI/TOML command checker.

## Handoff language

When you cannot verify a capability locally, be explicit:

- "Verified: import/config/CLI surface only."
- "Not verified: full SGLang/vLLM/Megatron/FSDP/Archon runtime because that requires matching CUDA packages, model weights, and/or cluster resources."
- "Next required live check: run the user's approved command in their target environment and capture logs/status/metrics."
