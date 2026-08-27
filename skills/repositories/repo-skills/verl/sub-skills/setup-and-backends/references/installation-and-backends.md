# Installation and Backend Setup

This reference distills verl setup facts for coding agents. It is self-contained and does not require access to the source repository used to generate the skill.

## Baseline requirements

- Python: verl declares `requires-python >=3.10`; current install docs commonly use Python 3.12 for CUDA environments and Python 3.10/3.11 in some backend-specific recipes.
- CUDA: current general installation docs require CUDA `>=12.8` for NVIDIA GPU runtime environments.
- Distribution version observed during skill generation: `verl 0.9.0.dev0`.
- Verified CPU inspection environment: imports succeeded for `verl`, `verl.protocol`, trainer config modules, `verl.trainer.main_ppo`, `verl.model_merger`, and `verl.tools.base_tool`; `pip check` passed.
- CPU inspection is not GPU runtime validation: optional CUDA/vLLM/SGLang/Megatron/flash-attn stacks were not installed in the verified inspection environment.

## Base installation patterns

### Docker-first runtime setup

Use Docker when preparing real accelerator training or rollout runtime because verl's inference and training backends pin large binary stacks and may override torch.

Current installation docs describe verl application images built on vLLM and SGLang base images. The images add packages such as `flash_attn`, Megatron-LM, Apex, TransformerEngine, and DeepEP. Typical Docker runtime requirements include NVIDIA runtime, all GPUs, host networking, adequate shared memory, and installing verl itself inside the container. If the image already contains the backend dependencies, install verl with `pip install --no-deps -e .`; if intentionally switching backend stacks, use extras such as `.[vllm]` or `.[sglang]` with care.

Use Docker as the default recommendation for:

- CUDA training or rollout execution.
- vLLM or SGLang backend validation.
- Megatron-LM/MCore setups with Apex, TransformerEngine, or custom kernels.
- Reproducible cluster bring-up where host system packages are hard to audit.

### Custom Python environment setup

Use a custom environment when Docker is unavailable or incompatible with the cluster. Start from a fresh environment to avoid accidental torch/backend overrides.

General flow:

1. Create a fresh Python environment with Python `>=3.10`.
2. Install the inference/training backend stack first when it has strict torch pins.
3. Install CUDA `>=12.8` and cuDNN `>=9.10.0` for NVIDIA runtime setups.
4. Install verl itself after backend prerequisites. For source installs inside an already prepared runtime image, `pip install --no-deps -e .` avoids replacing backend-pinned packages.
5. Re-check packages after every backend install because vLLM, SGLang, and torch-adjacent packages can overwrite each other.

Post-install packages worth checking include `torch`, torch extension packages, `vllm`, `sglang`, `pyarrow`, `tensordict`, and `nvidia-cudnn-cu12` for Megatron-oriented stacks.

## Dependency and extras map

Core installation metadata includes:

- `accelerate`, `codetiming`, `datasets`, `dill`, `hydra-core`, `numpy>=2.0.0`, `pandas`, `peft`, `pyarrow>=19.0.0`, `pybind11`, `pylatexenc`, `ray[default]>=2.41.0`, `torchdata`, `transformers!=5.6.0`, `wandb`, `packaging>=20.0`, `tensorboard`.
- `tensordict>=0.8.0,<=0.10.0,!=0.9.0`. This bound is important; latest or backend-installed tensordict versions outside the range can break verl even when torch imports.

Optional extras declared by the package:

- `test`: `pytest`, `pre-commit`, `py-spy`, `pytest-asyncio`, `pytest-rerunfailures`.
- `gpu`: `liger-kernel`, `flash-attn`.
- `math`: `math-verify`.
- `vllm`: `tensordict>=0.8.0,<=0.10.0,!=0.9.0`, `vllm>=0.8.5,<=0.12.0`.
- `sglang`: `tensordict>=0.8.0,<=0.10.0,!=0.9.0`, `sglang[srt,openai]==0.5.8`, `torch==2.9.1`.
- `mcore`: `mbridge`.
- `trtllm`: `tensorrt-llm>=1.2.0rc6`.
- Other declared extras include `prime`, `geo`, and `trl`.

Do not assume a base install includes any optional backend. Ask the user which runtime backend they need, or inspect package metadata with the bundled helper.

## Backend and platform matrix

### Training backends

- FSDP and FSDP2 are recommended for investigation, research, prototyping, and many standard workloads.
- Megatron-LM/MCore is recommended when scalability is the primary goal; current install docs cite Megatron-LM `v0.13.1` for the general CUDA path.
- The unified worker layer selects training backends at runtime through strategy fields such as `fsdp`, `fsdp2`, `megatron`, `automodel`, `veomni`, or `torchtitan`.

### Rollout and inference backends

- vLLM and SGLang are the primary rollout engines; Hugging Face TGI is usually for debugging or single-GPU exploration.
- Current install docs recommend vLLM `0.8.3+` for stability and mention `VLLM_USE_V1=1` for optimal vLLM performance. Package metadata for the `vllm` extra currently allows `vllm>=0.8.5,<=0.12.0`.
- The SGLang extra pins `sglang[srt,openai]==0.5.8` and `torch==2.9.1`, so install it in a fresh environment or before installing other torch-sensitive stacks.
- TensorRT-LLM support is optional through the `trtllm` extra and requires a compatible NVIDIA runtime stack.

### NVIDIA CUDA

- Current docs require CUDA `>=12.8` for real GPU runtime. Custom environments also need compatible cuDNN, often `>=9.10.0` in the documented CUDA path.
- vLLM 0.8+ with FSDP is supported. Older `vllm 0.7.x` should be avoided because project docs warn about OOMs and unexpected errors.
- FlashAttention and Liger kernels are optional GPU extras; absence is expected in CPU-only inspection environments.

### AMD ROCm

ROCm support is documented for AMD MI300X / MI325X (`gfx942`) and MI355X (`gfx950`) with:

- Runtime modes: Fully Async and Colocate.
- Inference engine: vLLM validated; SGLang support is ongoing.
- Trainer backends: FSDP, FSDP2, and Megatron.
- Example software baseline in docs: ROCm 7.0.2 and a prebuilt `amdagi/verl-dev:rocm7.0.2_56_te2.10_vllm0.20_py312` image.

PyTorch ROCm exposes a CUDA-like `torch.cuda` API, so code may still use the `cuda` device string while the platform vendor is AMD.

### Huawei Ascend NPU

Ascend support includes vLLM and SGLang inference with FSDP/FSDP2/Megatron training backends. The NPU docs describe separate version stacks for vLLM and SGLang paths, including `torch_npu`, CANN/HDK, Triton Ascend, and vLLM-Ascend or SGLang dependencies. Current notes say NPU device type can be auto-detected when `torch_npu` is installed; without `torch_npu`, users still need explicit NPU configuration.

For SGLang on NPU, the docs call out environment variables such as `HCCL_HOST_SOCKET_PORT_RANGE`, `HCCL_NPU_SOCKET_PORT_RANGE`, `RAY_EXPERIMENTAL_NOSET_ASCEND_RT_VISIBLE_DEVICES`, `ASCEND_RT_VISIBLE_DEVICES`, and `SGLANG_DEEPEP_BF16_DISPATCH`.

## Platform plugin behavior

verl registers built-in platform plugins for:

- `nvidia`: CUDA via `torch.cuda`, communication backend `nccl` by default or `flagcx` when `USE_FLAGCX=1`/`true`.
- `amd`: ROCm/HIP using the CUDA-compatible PyTorch API, with ROCm-specific Ray no-set environment variables and `SGLANG_USE_AITER` defaulting to `1` unless overridden.
- `huawei`: Ascend NPU via `torch_npu`/`torch.npu`, communication backend `hccl` by default or `flagcx` when requested.

Platform detection order:

1. `VERL_PLATFORM` environment variable, if set.
2. Registered platform probes using SMI/package checks.
3. Fallback to NVIDIA platform with a warning if no accelerator is detected.

External platform plugins can be registered through the platform registry and external-module loading mechanisms, but future agents should verify the plugin is installed and registered before relying on it.

## Practical setup decisions

- If the user only needs code inspection, config introspection, or import-level checks, a CPU environment is acceptable.
- If the user needs rollout or training execution, require a backend-specific GPU/NPU/ROCm environment and verify the accelerator before debugging Hydra overrides.
- If the user asks for vLLM rollout on a base install, check whether `vllm` is installed and in the supported range before changing verl code.
- If the user asks for SGLang rollout, check the SGLang extra pin and torch version first because the extra pins torch.
- If the user asks for Megatron/MCore, check for `mbridge`, Apex/TransformerEngine expectations, CUDA/NPU stack compatibility, and whether they really need Megatron rather than FSDP2.
- If Docker is allowed, prefer a documented prebuilt or project Dockerfile-derived image for accelerator runtime; if Docker is unsafe or unavailable, explain the custom environment risks and verify package versions after each install step.
