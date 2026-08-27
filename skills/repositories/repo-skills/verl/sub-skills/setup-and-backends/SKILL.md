---
name: setup-and-backends
description: "Install, inspect, and troubleshoot verl environments and
  accelerator backend stacks without constructing training commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# setup-and-backends

Use this sub-skill when a user needs verl installation guidance, environment inspection, accelerator/backend compatibility checks, Docker-vs-custom setup choices, or setup troubleshooting. Do not use it to build PPO/GRPO/SFT launch commands, rollout configs, checkpoint operations, or contribution-policy advice.

## Route by setup question

- For base installs, Python/CUDA requirements, optional extras, Docker images, or CPU-only package inspection, read [installation-and-backends.md](references/installation-and-backends.md).
- For vLLM, SGLang, Megatron-LM/MCore, TensorRT-LLM, GPU math/test extras, or platform plugin selection, read [installation-and-backends.md](references/installation-and-backends.md#backend-and-platform-matrix).
- For failed imports, tensordict/torch/backend version mismatches, CUDA not detected, Ray visible-device behavior, NPU/ROCm notes, or stale optional stacks, read [troubleshooting.md](references/troubleshooting.md).
- To gather safe local evidence from the active Python environment, run [check_verl_environment.py](scripts/check_verl_environment.py) and inspect its JSON output.

## Safe diagnostic helper

```bash
python sub-skills/setup-and-backends/scripts/check_verl_environment.py --pretty
python sub-skills/setup-and-backends/scripts/check_verl_environment.py --include-cuda --check-pip
```

The helper performs imports and package metadata checks only. It does not access the network, download models, launch Ray jobs, run Docker, or print local package file paths.

## Boundaries

- Keep installation advice self-contained; do not point future agents to source checkout docs, examples, scripts, or tests as runtime dependencies.
- Treat CPU-only environments as valid for import/config inspection but not as evidence that vLLM, SGLang, Megatron, flash-attn, TensorRT-LLM, CUDA kernels, ROCm, or NPU runtime jobs work.
- Prefer Docker images for accelerator runtime bring-up; use custom Python environments only when Docker is incompatible with the target system.
- Escalate hardware-specific failures to targeted checks before changing training configs: CUDA/ROCm/NPU visibility, torch build, backend package versions, Ray resource environment variables, and optional extras.
