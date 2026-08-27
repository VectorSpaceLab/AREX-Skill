# AReaL package overview

## What AReaL is

AReaL is a Python package for asynchronous LLM/VLM/agentic reinforcement learning and post-training. It combines:

- **Controller/trainer layer**: `PPOTrainer`, `SFTTrainer`, `DPOTrainer`, `RWTrainer` orchestrate datasets, rollout controllers, training controllers, evaluators, savers, and loggers.
- **Config layer**: dataclass configs in `areal.api.cli_args` are loaded from YAML plus CLI overrides by `load_expr_config()`.
- **Workflow layer**: rollout and agent workflows define how prompts, tool calls, model responses, logprobs, rewards, and tensor batches are produced.
- **Engine/backend layer**: FSDP2, Megatron, Archon, SGLang, vLLM, weight-update, LoRA, FP8, and parallelism utilities execute training/inference.
- **Infrastructure layer**: schedulers, launchers, RPC, data services, v2 inference/agent/training services, and operator CLI commands manage local/Ray/Slurm/service execution.

## Public package entry points

Minimal imports to know:

```python
import areal
from areal import PPOTrainer, SFTTrainer, DPOTrainer, RWTrainer
from areal.api.cli_args import GRPOConfig, PPOConfig, SFTConfig, DPOConfig, RWConfig, load_expr_config
from areal.dataset import get_custom_dataset
from areal.workflow.rlvr import RLVRWorkflow
from areal.workflow.vision_rlvr import VisionRLVRWorkflow
```

Console entry point:

```bash
areal --help
areal inf --help
areal agent --help
areal train --help
```

`areal inf` and `areal agent` operate v2 services. `areal train run` invokes a training driver with a config and overrides; high-level examples often call the driver script directly.

## Package layout by operating concern

| Concern | Modules | Route |
|---|---|---|
| Experiment configs | `areal.api.cli_args`, `areal.api.io_struct`, `areal.api.alloc_mode` | Root + `post-training-experiments` + `distributed-engines-backends` |
| Trainers and algorithms | `areal.trainer.*` | `post-training-experiments` |
| Datasets/rewards | `areal.dataset.*`, `areal.reward.*`, `areal.api.reward_api` | `custom-data-rewards-workflows` |
| Rollout and agent workflows | `areal.workflow.*`, `areal.api.workflow_api`, `areal.experimental.openai.*` | `custom-data-rewards-workflows` |
| Inference/training engines | `areal.engine.*`, `areal.experimental.engine.*`, `areal.models.*` | `distributed-engines-backends` |
| Schedulers/launchers/RPC | `areal.infra.*` | `distributed-engines-backends` and `services-cli-operations` |
| v2 services/CLI | `areal.v2.*` | `services-cli-operations` |
| Maintenance helpers | `areal.tools.*` | Use only for safe validation/profiling decisions; do not require original checkout at runtime |

## Installation variants

AReaL's runtime variants are mutually important:

| Variant | Use | Notes |
|---|---|---|
| Default CUDA/SGLang | Full training packages plus SGLang rollout | `uv sync --extra cuda`; requires Linux x86_64 CUDA-compatible environment for GPU execution. |
| vLLM CUDA | Full training packages plus vLLM rollout | Use the vLLM pyproject/lock pair before syncing; do not mix SGLang and vLLM pins casually. |
| Training-only CUDA | Training engines without an inference backend | Use `cuda-train` extra when rollout is external or service-managed. |
| CPU/import-only | Config, source, and script inspection | Suitable for lint/config/help checks only; not backend proof. |
| Sandbox | Daytona cloud sandbox integrations | Extra dependency and credentials/services may be required. |
| NPU/vendor accelerator | Ascend/NPU examples and branch-specific code | Requires vendor-specific runtime; treat as separate optional branch. |

## Verified construction facts

The generated skill's construction environment verified these public facts:

- Distribution metadata reports `areal` version `2.0.0`.
- Python support in package metadata is `>=3.11,<3.13`.
- Key imports succeeded for config, dataset, reward, RLVR/VLM workflows, v2 CLI, FSDP engine, and vLLM remote adapter modules.
- CLI groups are `areal inf`, `areal agent`, and `areal train`.
- CUDA was visible in the construction host, but the environment was not an exact full lockfile runtime. Treat backend execution guidance as evidence-backed but still requiring live verification in the user's target environment.

## Do not confuse these layers

- A successful `import areal` proves importability, not that CUDA backends, Ray, Slurm, SGLang, vLLM, Megatron, or Archon can run.
- `areal inf`/`areal agent` CLIs manage services; trainer scripts and `areal train run` manage training jobs.
- Dataset/reward/workflow contracts can be validated without launching training; actual algorithm behavior requires a configured trainer and target backend.
- Backend strings allocate role worlds; service model registration and process lifecycle are separate operations.
