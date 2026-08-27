# TorchRL Backend Compatibility

## Read this when

- A task asks for CUDA/ROCm/MPS behavior, Triton recurrent kernels, CUDA replay-buffer kernels, distributed collectors/replay, Ray/RPC/Submitit services, simulator wrappers, LLM serving, VLA datasets, or rendering/video.
- A CPU smoke passes but the user expects backend-specific evidence.
- An import fails only after selecting an optional TorchRL integration.

## Base CPU scope

TorchRL's core TensorDict-first workflows can be verified on CPU: native `PendulumEnv`, `TransformedEnv`, specs, local collectors, replay buffers, TensorDict modules, common losses, VLA schema validation, direct/process-style service concepts, and CLI help probes. CPU verification is a full substitute for those selected core behaviors.

CPU verification is only a partial or nonexistent substitute for these optional surfaces:

- CUDA replay-buffer kernels and CUDA extension behavior.
- Triton recurrent matmul/reset paths.
- GPU rollout/inference throughput and cudagraph/`torch.compile` hot paths.
- IsaacLab, Habitat, MuJoCo rendering, DM Control, Brax/JAX, Jumanji, PettingZoo, VMAS, OpenSpiel, Genesis, MJLab, or other simulator-specific wrappers.
- vLLM/SGLang LLM inference and weight synchronization.
- GRPO/RLHF training at model-serving scale.
- LeRobot/OpenX or other dataset/hub workflows that download data.
- Ray/RPC/Submitit/Monarch distributed services and multi-node launchers.
- Video/render codecs and notebook viewer stacks.

## Backend probe checklist

Use the smallest relevant probe for the requested backend:

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print('cuda available', torch.cuda.is_available(), 'count', torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty(1, device='cuda')
PY
```

For source CUDA builds, also check the host compiler and toolkit:

```bash
nvidia-smi
nvcc --version
```

For optional simulator packages, first import only the wrapper or backend package and construct a tiny environment only if it does not download data or start external services. For LLM serving, do not start vLLM/SGLang or download a model unless the user provisioned model paths, GPUs, and runtime budget.

## How to report backend status

- `verified`: the requested backend-specific import and minimal operation passed in the active environment.
- `cpu-verified`: the CPU alternative verifies the same selected behavior; do not use this label for GPU-only kernels or serving.
- `optional-unverified`: guidance is present, but the dependency/hardware/service was not installed or exercised.
- `blocked-required-backend`: the user requested a backend whose CPU substitute is partial or none, and the environment cannot prove it.

If a backend is optional and unverified, keep it out of final success claims. If it is required for the user's task, stop and ask for compatible hardware/environment or narrow the task scope.

## Common backend-specific failure patterns

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `torch.cuda.is_available()` is false on a GPU host | CPU-only PyTorch wheel, driver/container passthrough issue, incompatible CUDA runtime | Install a compatible PyTorch CUDA wheel or run inside a GPU-enabled container; rerun the tensor allocation probe. |
| TorchRL source build skips CUDA extension | `nvcc` missing, CUDA_HOME unset, or nvcc CUDA version mismatches PyTorch CUDA | Use CPU extension if CUDA kernels are not required; otherwise install matching toolkit/compiler and rebuild. |
| `ImportError` for Gym/MuJoCo/DM Control/Brax/Jumanji/PettingZoo/VMAS/OpenSpiel | Optional simulator extra not installed | Install only the named backend extra/package and run the wrapper's minimal import/env smoke. |
| Ray collector/replay/service fails at import | Ray optional dependency absent | Install Ray only for distributed/service-backed workflows; keep direct/process workflows CPU-verified. |
| vLLM/SGLang wrapper fails or hangs | Serving backend absent, GPU memory insufficient, model download/cache unavailable, server not running | Verify backend install, model path/cache, tokenizer, ports, and weight-sync topology before invoking collectors. |
| VLA dataset loader fails | LeRobot/OpenX/offline-data dependencies or dataset cache absent | Validate a tiny VLA TensorDict schema first; install dataset extras and acquire data only when the workflow requires it. |
| `rlrender` produces no video/window | Rendering extra, codec, display, simulator pixels, or policy/env factory missing | Use `--help`, `--validate-only`, `--dry-run`, and simple native envs before requesting video artifacts. |
