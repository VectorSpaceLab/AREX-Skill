---
name: operations-and-utilities
description: "Install, diagnose, and operate OpenRLHF runtime utilities,
  including optional GPU dependencies, Ray/NCCL environment propagation, reward
  model serving, LoRA merging, DeepSpeed checkpoint conversion, and
  Docker/system caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenRLHF Operations and Utilities

Use this sub-skill when the task is about getting OpenRLHF installed, checking runtime readiness, configuring Ray/vLLM/DeepSpeed environment variables, serving a reward model, merging LoRA adapters, converting DeepSpeed checkpoints, or interpreting Docker/system helper scripts.

Do not use this sub-skill to design SFT/RM/DPO/PPO training recipes, tune dataset schemas, or explain RL agent workflows. Route those to the training, RL, or data-preparation sub-skills, then return here only for runtime diagnostics or utility commands.

## Fast Route

1. For install choices, optional extras, Docker, CUDA/flash-attn, vLLM, DeepSpeed, Ray, and lightweight health checks, read `references/installation-and-runtime.md`.
2. For utility commands such as reward model serving, LoRA merging, and DeepSpeed ZeRO-to-universal checkpoint conversion, read `references/utilities.md`.
3. For failure triage, especially flash-attn build order, CUDA/wheel mismatch, Ray env var preservation, reward server load/port issues, LoRA merge pitfalls, checkpoint conversion safety, and logger credential problems, read `references/troubleshooting.md`.
4. For a safe local diagnostic that avoids importing heavy OpenRLHF internals, run:

```bash
python skills/openrlhf/sub-skills/operations-and-utilities/scripts/check_openrlhf_runtime.py
```

## Safety Classification

- Safe/lightweight: inspect package metadata, import availability for dependency names, environment variables, Python version, and `torch.cuda.is_available()` if `torch` is already installed.
- Potentially expensive: importing `torch`, checking CUDA, installing `openrlhf[vllm]`, starting `ray`, loading HuggingFace models, merging LoRA weights, or serving reward models.
- GPU/service/system actions: treat Docker installation, NVIDIA runtime setup, Ray cluster startup, vLLM/DeepSpeed training utilities, reward model servers, and checkpoint conversion as user-approved operations only.

## Evidence Anchors

This sub-skill is based on OpenRLHF repository evidence from `README.md`, `requirements.txt`, `setup.py`, `dockerfile/Dockerfile`, `dockerfile/docker-entrypoint.sh`, `examples/scripts/serve_remote_rm.sh`, `examples/scripts/ckpt_ds_zero_to_universal.sh`, `examples/scripts/docker_run.sh`, `examples/scripts/nvidia_docker_install.sh`, `openrlhf/cli/serve_rm.py`, `openrlhf/cli/lora_combiner.py`, `openrlhf/cli/train_ppo_ray.py`, `openrlhf/utils/deepspeed/`, `openrlhf/utils/utils.py`, `tests/test_ray_env_vars.py`, and `tests/test_loss_aggregation.py`.
