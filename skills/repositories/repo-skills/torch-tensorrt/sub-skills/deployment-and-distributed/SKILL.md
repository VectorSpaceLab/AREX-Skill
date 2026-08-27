---
name: deployment-and-distributed
description: "Use this sub-skill for Torch-TensorRT deployment artifacts, Triton
  serving, C++ or AOTInductor execution, ExecuTorch export, TensorRT-RTX
  platforms, DLA/Jetson, Windows cross-compile, and distributed inference."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Torch-TensorRT Deployment and Distributed Inference

Use this sub-skill when the question is not just "how do I compile?" but "where and how will the compiled result run?"

## Choose the deployment target first

| Target | Typical artifact/API | Read |
| --- | --- | --- |
| Python deployment | `.ep`, `torch.export.load(...).module()`, `torch_tensorrt.load(...)` | `references/artifact-deployment-matrix.md` |
| C++/libtorch | `.ts`, `torch::jit::load`, Torch-TensorRT runtime libraries | `references/cpp-aoti-executorch.md` |
| AOTInductor | `.pt2`, `torch._inductor.aoti_load_package`, C++ AOTI loader | `references/cpp-aoti-executorch.md` |
| Triton serving | model repository, `config.pbtxt`, client requests | `references/triton-and-serving.md`; `scripts/generate_triton_config.py --help` |
| Raw TensorRT runtime | `.engine` bytes | `../compilation-and-export/references/serialization-and-engines.md` |
| ExecuTorch | `.pte` with ExecuTorch runtime | `references/cpp-aoti-executorch.md` |
| Distributed inference | `torchtrtrun`, `distributed_context`, NCCL/TRT collectives | `references/distributed-inference.md`; `scripts/torchtrtrun_env_probe.py --help` |
| Platform-specific deployment | TensorRT-RTX, DLA/Jetson, Windows x86-64 cross-compile, Windows ARM64 build | `references/platforms-and-rtx.md` |

## Deployment workflow

1. Identify the target process: Python, C++, Triton server, raw TensorRT runtime, ExecuTorch, Windows, Jetson/DLA, or multi-GPU/distributed.
2. Verify the needed feature gates and runtime libraries on both build and target machines.
3. Compile with the right artifact in mind. Some choices must be made before save/export, such as `output_format`, `hardware_compatible`, dynamic shapes, and runtime support.
4. Save the artifact and test load/execute in the closest available target runtime.
5. Package supporting files: Triton model repository, C++ library path, AOTI loader, NCCL environment, runtime cache directories, or Windows/Jetson prerequisites.

## Common deployment decisions

- Use `.ep` for Python deployment where PyTorch remains available.
- Use `.ts` only when the Torch-TensorRT C++ runtime is available and the target uses libtorch/TorchScript.
- Use `.pt2` AOTInductor on Linux when the user wants a package runnable without importing Torch-TensorRT at inference time.
- Use raw `.engine` when the entire graph must be TensorRT-only and no PyTorch fallback is allowed.
- Use TensorRT-RTX for RTX desktop/laptop/workstation targets and RTX-specific runtime JIT behavior.
- Use DLA only on supported embedded platforms and only with FP16/INT8.
- Use `torchtrtrun` and `distributed_context` for distributed inference with TensorRT collectives/NCCL concerns.

## Guardrails

- Do not tell users to copy files from the original source checkout. Use the recipes and bundled scripts here.
- Do not run Triton servers, multi-rank jobs, Docker, network clients, or C++ builds unless the user explicitly asks and the environment is prepared.
- Do not promise a Python-only Torch-TensorRT wheel can support C++ runtime or TorchScript artifact execution.
- Do not treat a model artifact as portable across TensorRT versions, GPU compute capabilities, CUDA versions, or package flavors unless `hardware_compatible`/`version_compatible` and target testing support that claim.
