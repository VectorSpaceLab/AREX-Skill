# ExecuTorch Package Overview

## Purpose

Read this when you need the repo-level mental model before choosing a sub-skill. This file distills the public source layout and package surfaces into operating guidance; it is not a replacement for the focused sub-skills.

## Core Concepts

- ExecuTorch converts PyTorch programs into `.pte` files for edge runtimes. Program-data separation may also produce `.ptd` tensor-data files.
- Export normally begins with a PyTorch `nn.Module` in `eval()` mode and representative example inputs.
- Backends/delegates specialize part or all of the graph for target hardware. Unsupported nodes may fall back to portable CPU kernels when the backend and export path support fallback.
- Runtime integration can happen through Python pybindings for host validation, C++ low-level APIs, higher-level C++ `Module`/`Tensor` extensions, Android Java/Kotlin bindings, Apple frameworks, or model-specific runners.

## Public Package Areas

| Area | What it owns | Typical user signal |
| --- | --- | --- |
| `executorch.exir` | EXIR lowering, `to_edge`, `to_edge_transform_and_lower`, backend config, serialization helpers | `.pte`, edge dialect, partitioner, memory planning |
| `executorch.export` | Higher-level export sessions and recipes | `ExportRecipe`, `QuantizationRecipe`, multi-stage export pipeline |
| `executorch.runtime` | Python runtime loading/execution when pybindings are built | `Runtime.get()`, `load_program`, `load_method`, `execute` |
| `executorch.extension.pybindings` | Portable pybinding loader and `.pte` + `.ptd` support | `_load_for_executorch`, missing `_portable_lib` |
| `executorch.devtools` | ETRecord/ETDump inspection, profiling, visualization, debug artifacts | `Inspector`, ETDump, ETRecord, delegate debug |
| `executorch.backends.*` | Backend partitioners, quantizers, preprocessors, build integration | XNNPACK, QNN, Core ML, MPS, Vulkan, CUDA, OpenVINO, Arm |
| `extension/*`, `runtime/*`, `kernels/*`, `backends/*` | C++ runtime, extensions, kernels, delegates | CMake, linker flags, static libraries, mobile/embedded runtime |

## Artifact Names

- `.pte`: ExecuTorch program file.
- `.ptd`: optional tensor-data file for separated constants/weights.
- ETRecord: export-time debug metadata that maps runtime events back to graph/source/module hierarchy.
- ETDump: runtime-collected performance/debug blob.
- BundledProgram: program plus representative inputs/expected outputs for runtime validation.

## Terminology Rules

Use "ExecuTorch" for prose and `executorch` for the package/import name. Avoid "ExecutorTorch". Use "ET" only when brevity matters and the surrounding context is unambiguous.

