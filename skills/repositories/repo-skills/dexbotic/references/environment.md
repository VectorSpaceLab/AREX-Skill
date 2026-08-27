# Dexbotic environment and backend matrix

## Package facts

- Distribution: `dexbotic==0.2.0`
- Python: `>=3.10`
- Core stack includes PyTorch/VLA/data/web dependencies; exact compatible versions are deployment-specific.
- The inspected core stack successfully imported Dexbotic client, dataset, policy, experiment, and representative model modules.

## Required core backend

Core VLA model training/inference is CUDA-required for the broad scope. A valid environment must import PyTorch and allocate a tiny CUDA tensor on the intended GPU. The inspected verification host exposed NVIDIA A100-class GPUs and passed that smoke, but this is evidence for the inspection snapshot, not a portable hardware guarantee. If CUDA is unavailable, narrow claims to API/configuration/data guidance and do not call it a verified core runtime.

The repository documents Python 3.10 and CUDA 11.8-oriented PyTorch 2.6-era combinations. The backend resolver additionally checks torch, Transformers, Accelerate, and optional DeepSpeed versions for FSDP/DeepSpeed choices. Prefer an isolated environment and consult the resolver rather than copying a source-tree-relative dependency pin blindly.

## Optional variants

| Surface | Prerequisites | Verification limit |
|---|---|---|
| DDP | CUDA and distributed launcher | No distributed training by default; use bounded smoke only. |
| DeepSpeed | CUDA plus compatible DeepSpeed and launcher | Config/help/resolver checks; no full job. |
| FSDP/FSDP2 | CUDA, compatible torch/Transformers/Accelerate, explicit config/profile | Resolver/config checks; no multi-GPU training. |
| DM0 realtime | CUDA, Triton-compatible stack, converted checkpoint | Import/help only unless matching weights/backend are explicitly prepared. |
| flash-attn/xformers/kernels | Optional compiled/runtime attention packages | Fallback attention may work; extension-specific performance is unverified. |
| Simulators/benchmarks | External assets and packages | No broad simulator install or long evaluation. |
| RLinf/SimpleVLA-RL | External distributed RL runtime and embodied environments | Core package import does not verify this surface. |
| LeRobot/robot SDKs | External package, cameras, serial/network hardware | Conversion/parser checks only; no device I/O. |

## Safe probes

Use `scripts/check_environment.py` for package/CUDA/import diagnostics and `scripts/validate_skill_links.py` for the generated runtime tree. These probes are read-only and do not activate environments or install packages.
