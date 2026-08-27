---
name: colossal-ai
description: "Use ColossalAI for distributed PyTorch training, large-model
  parallelism, Booster plugins, ShardFormer, Colossal-Inference, and first-party
  application workflow routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ColossalAI

Use this skill when the task names ColossalAI, `colossalai`, `colossalai run`, `Booster`, `GeminiPlugin`, `HybridParallelPlugin`, `ShardFormer`, Colossal-Inference, ColossalChat, Colossal-LLaMA, ColossalEval, ColossalQA, or ColossalMoE.

ColossalAI is a Linux-oriented distributed PyTorch and large-model system. Most meaningful training and inference workflows require CUDA-capable PyTorch, `torchrun` or ColossalAI launch setup, and model/data assets chosen by the user.

## Quick Start

1. Verify the package and backend before giving GPU or distributed advice:
   ```bash
   python scripts/check_colossalai_environment.py --check-cli
   ```
2. Route to the focused sub-skill for detailed commands and recovery steps.
3. Keep hardware, model weights, datasets, credentials, and optional extensions explicit. Do not promise a CUDA, Apex, flash-attn, TensorNVMe, vLLM, or application package path until that dependency is installed and checked.
4. Prefer synthetic or helper-generated command checks before running long training, benchmark, model-download, or service workflows.

## Route By Task

- **Install, check, and launch**: use `sub-skills/installation-and-launch/SKILL.md` for installation variants, `colossalai check -i`, `colossalai run`, hostfiles, `torchrun`, SLURM/OpenMPI launch APIs, and port/NCCL startup failures.
- **Booster training**: use `sub-skills/booster-training/SKILL.md` for `Booster`, plugin selection, training loop structure, dataloaders, checkpointing, LoRA, mixed precision, ZeRO, Gemini, and memory-aware training.
- **Parallelism and sharding**: use `sub-skills/parallelism-and-sharding/SKILL.md` for tensor/pipeline/sequence parallelism, ShardFormer, topology sizing, auto-parallel, activation checkpointing, NVMe offload, and process-group reasoning.
- **Inference and serving**: use `sub-skills/inference-and-serving/SKILL.md` for `InferenceConfig`, `InferenceEngine`, LLM generation, speculative decoding, Stable Diffusion 3 patched parallelism, serving/client benchmarks, and inference errors.
- **First-party applications**: use `sub-skills/application-recipes/SKILL.md` for ColossalChat/Coati, Colossal-LLaMA, ColossalEval, ColossalQA, and ColossalMoE environment isolation, command anatomy, and limitations.

## Core Import and CLI Signals

```bash
python - <<'PY'
import colossalai, torch
print('colossalai', colossalai.__version__)
print('torch', torch.__version__, 'cuda', torch.version.cuda, 'available', torch.cuda.is_available())
PY
colossalai --help
colossalai check -i
```

Use `colossalai check -i` to distinguish PyTorch CUDA compatibility, system CUDA visibility, and AOT extension build information. `System CUDA version: N/A` usually means `CUDA_HOME` or `nvcc` is not visible; PyTorch CUDA wheels can still run CUDA kernels when the driver supports them.

## Cross-Cutting References and Helpers

- `references/installation.md` summarizes package, Python, PyTorch, CUDA, and optional extension constraints that affect all workflows.
- `references/troubleshooting.md` covers install/import/backend/CLI/distributed failures that are not owned by one sub-skill.
- `references/testing-and-verification.md` lists safe checks, native candidates, and expensive examples to avoid by default.
- `references/repo-provenance.md` records the source revision, package version, and evidence paths used to build this skill.
- `scripts/check_colossalai_environment.py` performs a safe import, version, CUDA, and optional CLI-help diagnostic without downloading models or starting services.

## Operating Rules

- Initialize distributed state before constructing most Booster plugins. For ordinary scripts, use `torchrun` or `colossalai run`; for manual setup, call `colossalai.launch(...)` with rank/world size/host/port.
- Treat app packages as separate environments unless proven compatible. The core ColossalAI package uses modern PyTorch; ColossalQA and some application stacks pin older or conflicting dependencies.
- Do not run benchmark-scale examples, large model generation, multi-node jobs, or service listeners unless the user has supplied assets, hardware, and approval.
- Do not route generic PyTorch, DeepSpeed, Lightning, Transformers, vLLM, or LangChain tasks here unless ColossalAI owns the launcher, plugin, sharding, inference, or application workflow in the user request.
