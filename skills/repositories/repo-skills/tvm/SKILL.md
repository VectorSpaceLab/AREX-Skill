---
name: tvm
description: "Guides Apache TVM install/build, Relax compilation, TIRx kernel
  authoring, S-TIR tuning, and RPC deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Apache TVM Repo Skill

Use this skill when a task involves Apache TVM as a machine-learning compiler
stack: installing or building TVM, compiling Relax/TIR modules, authoring TIRx
kernels, scheduling/tuning tensor programs, or deploying through TVM RPC.

This is a router. Read the focused sub-skill before making detailed API,
configuration, backend, or verification decisions.

## Fast routing

| User task signal | Read |
|---|---|
| Build from source, validate import, choose CMake/LLVM/RPC/CUDA flags, fix `libtvm` or `tvm-ffi` import failures | [`sub-skills/install-build/SKILL.md`](sub-skills/install-build/SKILL.md) |
| Create or import Relax IR, apply optimization pipelines, call `tvm.compile`, export/load executables, decide target/pipeline boundaries | [`sub-skills/relax-compile/SKILL.md`](sub-skills/relax-compile/SKILL.md) |
| Write TIRx TVMScript kernels, reason about execution scope, layouts, tile primitives, lowering, CUDA/Blackwell prerequisites, or TIRx GPU tests | [`sub-skills/tirx-kernels/SKILL.md`](sub-skills/tirx-kernels/SKILL.md) |
| Use `tvm.s_tir.Schedule`, transformations, dlight, meta-schedule, `tune_tir`, builders/runners/databases, or tune CPU/GPU TIR | [`sub-skills/s-tir-tuning/SKILL.md`](sub-skills/s-tir-tuning/SKILL.md) |
| Start/query TVM RPC tracker/server/proxy, cross-compile, upload/load remote modules, debug keys/timeouts/target-host issues | [`sub-skills/rpc-deployment/SKILL.md`](sub-skills/rpc-deployment/SKILL.md) |

## Minimal install/import orientation

- Distribution name: `apache-tvm`; import name: `tvm`.
- A package install starts with `python -m pip install apache-tvm`; add optional
  dependencies only for the selected workflow, such as meta-schedule, RPC,
  Torch frontend, or CUDA helper packages.
- Core runtime dependencies from package metadata include `apache-tvm-ffi`,
  `numpy`, `ml_dtypes`, and `typing_extensions`.
- Optional extras are workflow-specific: `meta-schedule` adds `xgboost`, `rpc`
  adds `tornado`, `psutil`, and `cloudpickle`, `popen-pool` adds `psutil` and
  `cloudpickle`, `torch` adds `torch`, and `cuda` adds `cuda-bindings`.
- For a source checkout, prefer a built `build/` directory plus `PYTHONPATH`
  pointing at the checkout's `python/` tree. Avoid editable installs when
  working with multiple TVM checkouts because they can silently import a
  different checkout's Python package.

Minimal verification from this skill directory:

```bash
python scripts/check_tvm_runtime.py --expect-backend llvm
```

Use [`scripts/check_tvm_runtime.py`](scripts/check_tvm_runtime.py) for a safe
import/backend probe against an installed package or a caller-provided checkout.
Read [`references/troubleshooting.md`](references/troubleshooting.md) when an
import, runtime library, backend, or optional dependency mismatch appears.

## Backend truthfulness rules

- A CPU/LLVM import check proves only CPU/LLVM readiness. It does not prove CUDA,
  ROCm, Metal, Vulkan, RPC device execution, TIRx GPU execution, or Blackwell
  kernel-library correctness.
- TVM can compile for a target without a matching local device in some cases, but
  execution and timing require the target runtime/device to exist.
- TIRx Blackwell and external `tirx-kernels` workflows require compute capability
  10.0-class NVIDIA hardware and additional packages. Do not present them as
  verified from an A100/CPU-only environment.

## Verify before relying on this skill

Read [`references/repo-provenance.md`](references/repo-provenance.md) before
assuming this skill matches a different checkout or release. Refresh the skill
when the commit, major package metadata, public API shape, or TIRx/S-TIR/RPC
workflow evidence changes.

Structured router metadata lives in
[`references/repo-routing-metadata.json`](references/repo-routing-metadata.json).
