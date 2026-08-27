---
name: torch-tensorrt
description: "Use this skill for Torch-TensorRT tasks: compiling PyTorch models
  with TensorRT, dynamic-shape/export workflows, runtime optimization,
  Triton/C++/distributed deployment, debugging unsupported ops, and maintaining
  source builds."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Torch-TensorRT

Torch-TensorRT accelerates PyTorch inference on NVIDIA GPUs by compiling supported graph regions into TensorRT engines while keeping PyTorch integration for the rest of the workflow. Use this root as a router first; load sub-skills for detailed procedures.

## When to use this skill

Use this skill when the request mentions any of these signals:

- Torch-TensorRT, `torch_tensorrt`, `torch-tensorrt`, `torch-tensorrt-rtx`, TensorRT-RTX, `backend="torch_tensorrt"`, `ir="dynamo"`, or `torchtrtrun`.
- PyTorch-to-TensorRT inference compilation, `torch.export` plus TensorRT, TensorRT engine serialization, `.ep`, `.ts`, `.pt2`, `.engine`, or `.pte` artifacts.
- Dynamic TensorRT input shapes, optimization profiles, `Input(...)`, `Device(...)`, precision settings, unsupported-op fallback, `dryrun`, custom converters, TensorRT plugins, or QDP kernels.
- CUDA Graphs, engine caches, runtime settings, mutable Torch-TensorRT modules, refit, weight streaming, Triton serving, C++ runtime, ExecuTorch, DLA/Jetson, Windows cross-compile, or distributed inference.

Do not use this skill for generic PyTorch training, generic TensorRT C++ applications with no PyTorch/Torch-TensorRT layer, or unrelated model-serving frameworks unless Torch-TensorRT artifacts are part of the task.

## First checks

1. Confirm the user has, or is willing to prepare, an NVIDIA GPU runtime with compatible CUDA, PyTorch, TensorRT or TensorRT-RTX, and `torch_tensorrt` installed.
2. If the package is missing, start with a matching public install command and then narrow the environment from there:

   ```bash
   python -m pip install torch torch-tensorrt tensorrt
   # or, for the RTX variant
   python -m pip install torch torch-tensorrt-rtx
   ```

   Adjust CUDA/PyTorch versions to the user's platform before promising success.
3. Run the bundled environment probe when install state is uncertain:

   ```bash
   python scripts/check_torch_tensorrt_env.py --no-cuda-smoke
   ```

   The script is safe: it imports packages, prints versions/features, and only allocates a tiny CUDA tensor when CUDA is visible.
4. Read `references/installation-and-features.md` before giving install advice, choosing standard TensorRT versus TensorRT-RTX, diagnosing optional features, or interpreting `ENABLED_FEATURES`.
5. Read `references/api-surface-map.md` when the user names an API but it is unclear which sub-skill owns it.
6. Read `references/troubleshooting.md` when the first visible symptom is an import, CUDA, TensorRT wheel, serialization, quantization, or unsupported-op error.

## Route by task

| User goal | Load this sub-skill |
| --- | --- |
| Compile a model through `torch.compile`, `torch_tensorrt.compile`, `torch.export`, dynamic shapes, precision/settings, save/load, raw engine extraction, or Windows cross-compile API choices | `sub-skills/compilation-and-export/SKILL.md` |
| Optimize a compiled module at runtime: CUDA Graphs, output allocator, preallocated outputs, weight streaming, engine/timing/runtime caches, TensorRT-RTX runtime settings, mutable modules, refit, benchmarking, memory triage | `sub-skills/runtime-optimization/SKILL.md` |
| Deploy compiled artifacts to Python, C++, AOTInductor, Triton, ExecuTorch, DLA/Jetson, Windows/ARM64, TensorRT-RTX, or distributed inference with `torchtrtrun` | `sub-skills/deployment-and-distributed/SKILL.md` |
| Debug or extend compiler behavior: `dryrun`, `Debugger`, capture/replay, unsupported ops, converter/lowering/plugin authoring, QDP kernels, ModelOpt/quantization warnings, issue-quality repros | `sub-skills/extensibility-and-debugging/SKILL.md` |
| Build or test Torch-TensorRT from source, choose package variants, inspect CI/test lanes, or maintain repository code | `sub-skills/build-and-maintenance/SKILL.md` |

## Repository-specific operating rules

- Prefer the Dynamo path for new Python workflows: `torch.compile(..., backend="torch_tensorrt")`, `torch_tensorrt.compile(..., ir="dynamo")`, or `torch.export.export(...)` followed by `torch_tensorrt.dynamo.compile(...)`.
- Treat the legacy TorchScript/C++ APIs as real but specialized. Route them through deployment or build/maintenance when the task explicitly needs `.ts`, C++/libtorch, DLA, or source builds.
- Always state backend prerequisites and feature gates before promising execution. Standard TensorRT, TensorRT-RTX, QDP kernels, ModelOpt quantization, distributed/NCCL, ExecuTorch, and C++ runtime features have different package and platform requirements.
- Do not instruct the user to run examples or scripts from an original source checkout. Use the bundled references and scripts in this skill, or write task-local code for the user.
- For performance claims, require user-side measurement with warmups, CUDA synchronization/events, representative dynamic shapes, and a PyTorch baseline. Do not infer speedups from compile success alone.
- For unsupported operators, first decide whether fallback is acceptable. Use `dryrun`, `torch_executed_ops`, `min_block_size`, or model rewrites before recommending custom converter/plugin work.

## Evidence and refresh

- Source snapshot and evidence map: `references/repo-provenance.md`.
- Router metadata for managed imports: `references/repo-routing-metadata.json`.
- This skill was generated from source and documentation evidence plus a partial installed-package inspection. The inspection proved imports and a tiny TensorRT-RTX Dynamo compile, but did not prove all standard TensorRT, C++ runtime, serialization, distributed, QDP, or ModelOpt paths. Preserve those limits in downstream advice unless the user's current environment verifies them.
