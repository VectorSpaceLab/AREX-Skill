# Installation and Runtime

Use this reference for OpenRLHF install choices, optional dependency boundaries, CUDA/flash-attn/vLLM/DeepSpeed caveats, Ray environment behavior, Docker notes, and lightweight diagnostics.

## Verified Package Facts

- Python distribution: `openrlhf`.
- Verified version in the inspected package environment: `0.10.4`.
- Verified top-level import: `import openrlhf`.
- Full dependency/runtime readiness was not verified: full dependency installation can require GPU-compatible `torch`, CUDA/NVCC, `flash-attn`, DeepSpeed, Ray, vLLM, and large model downloads.

## Install Choices

OpenRLHF declares Python `>=3.10` and installs base dependencies from `requirements.txt`, including `torch`, `deepspeed==0.19.1`, `flash-attn==2.8.3`, `ray[default]==2.55.0`, `transformers==5.7.0`, `peft`, `bitsandbytes`, `wandb`, and `pynvml>=12.0.0`.

The package extras in `setup.py` are:

| Extra | Adds | Use when |
| --- | --- | --- |
| base `openrlhf` | core requirements | You only need package import, CLI discovery, or non-vLLM utilities. |
| `openrlhf[vllm]` | `vllm==0.22.1` | Recommended runtime path in the README for vLLM-backed RL training. |
| `openrlhf[vllm_latest]` | `vllm>0.22.1` | You intentionally want newer vLLM behavior and can handle compatibility drift. |
| `openrlhf[ring]` | `ring_flash_attn` | You use RingAttention flags such as `--ds.ring_attn_size`. |
| `openrlhf[liger]` | `liger_kernel` | You need Liger optimizations. |

Example install commands from the repository docs:

```bash
pip install openrlhf
pip install 'openrlhf[vllm]'
pip install 'openrlhf[vllm,ring,liger]'
```

For source development:

```bash
git clone https://github.com/OpenRLHF/OpenRLHF.git
cd OpenRLHF
pip install -e .
```

Do not claim a machine is GPU-ready after only `import openrlhf`; check the relevant CUDA, `torch`, DeepSpeed, vLLM, and model-loading path.

## Docker and System Notes

The README recommends Docker for hassle-free setup and shows an NVIDIA runtime container with shared memory and `SYS_ADMIN`:

```bash
docker run --runtime=nvidia -it --rm --shm-size="10g" --cap-add=SYS_ADMIN \
  -v "$PWD:/openrlhf" nvcr.io/nvidia/pytorch:26.03-py3 bash
```

The repository Dockerfile uses `nvcr.io/nvidia/pytorch:26.03-py3`, installs system build packages, removes potentially conflicting packages, installs `vllm==0.22.1`, then builds `flash-attn==2.8.3` with `--no-build-isolation` after vLLM has pulled its matching `torch` build. This supports a common troubleshooting principle: install or provide the intended `torch`/CUDA stack before building `flash-attn`.

Treat `examples/scripts/nvidia_docker_install.sh` as reference-only unless the user explicitly approves system mutation. It removes old Docker packages, installs Docker through `curl https://get.docker.com | sh`, adds NVIDIA container toolkit repositories, runs `apt-get`, configures Docker runtime with `nvidia-ctk`, edits user groups, and invokes `newgrp docker`.

Treat `examples/scripts/docker_run.sh` as a reference template. It mounts the repository and `$HOME/.cache` into the container and starts `nvcr.io/nvidia/pytorch:26.03-py3`.

## CUDA, flash-attn, vLLM, and DeepSpeed Caveats

- `flash-attn==2.8.3` is in base requirements, but builds are sensitive to `torch`, CUDA toolkit/NVCC, compiler, and wheel availability.
- If installation fails before `torch` metadata exists, install the intended GPU-compatible `torch` stack first or use a container/wheel combination that already matches the target CUDA runtime.
- If `nvcc` is missing, a source build of `flash-attn` may fail even if a CUDA driver is present. Driver-only CUDA is not the same as a build toolkit.
- vLLM is optional via package extras but central to high-throughput OpenRLHF RL examples. The README recommends vLLM `0.22.1+`, while `setup.py` pins `openrlhf[vllm]` to `vllm==0.22.1`.
- DeepSpeed is required by the base requirements and is used for training, optimizer configuration, ZeRO checkpoints, universal checkpoint conversion, and memory-saving strategies.
- RingAttention requires the `ring` extra and source code imports `ring_flash_attn` only when ring attention is enabled.

## Ray Environment Variables

`openrlhf.cli.train_ppo_ray.train()` initializes Ray with a `runtime_env.env_vars` dictionary when Ray is not already initialized. The code preserves user-provided values through `os.environ.get()` and falls back to defaults:

| Variable | Default | Behavior |
| --- | --- | --- |
| `TOKENIZERS_PARALLELISM` | `true` | Passed into Ray workers unless user sets another value. |
| `NCCL_DEBUG` | `WARN` | User values such as `INFO` or `TRACE` are preserved. |
| `RAY_ENABLE_ZERO_COPY_TORCH_TENSORS` | `1` | User can set `0` to disable. |

The tests in `tests/test_ray_env_vars.py` mock Ray and assert these defaults and user overrides. If a user reports `NCCL_DEBUG=INFO` is ignored, check where the variable is set relative to `ray job submit`, `ray.init()`, and any shell/container boundary. For Ray job submission, prefer passing environment through the job runtime environment or exporting it in the shell that launches the job.

Example runtime env snippet:

```bash
ray job submit --address="http://127.0.0.1:8265" \
  --runtime-env-json='{"env_vars":{"NCCL_DEBUG":"INFO","TOKENIZERS_PARALLELISM":"false"},"setup_commands":["pip install openrlhf[vllm]"]}' \
  -- python3 -m openrlhf.cli.train_ppo_ray ...
```

The README also notes `RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES=1` for DeepSpeed GPU device setup/index issues.

## Lightweight Runtime Diagnostic

Run the bundled diagnostic before attempting GPU or service work:

```bash
python skills/openrlhf/sub-skills/operations-and-utilities/scripts/check_openrlhf_runtime.py
```

The script reports:

- Python executable/version.
- `openrlhf` distribution metadata and top-level import availability.
- Presence of key optional packages such as `torch`, `deepspeed`, `ray`, `vllm`, `flash_attn`, `ring_flash_attn`, `liger_kernel`, `peft`, `bitsandbytes`, `wandb`, and `pynvml`.
- `torch` version and CUDA status if `torch` is importable.
- Environment variables `NCCL_DEBUG`, `TOKENIZERS_PARALLELISM`, `RAY_ENABLE_ZERO_COPY_TORCH_TENSORS`, `RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES`, and selected CUDA-related variables.

The diagnostic intentionally does not import OpenRLHF internals, start Ray, load models, run DeepSpeed, or require GPUs.
