---
name: runtime-ops
description: "Route Det3D installation, import, CUDA extension, PyTorch ABI,
  optional dependency, distributed-runtime, and checkpoint filesystem
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Runtime Operations

Use this route whenever Det3D fails during installation, package import, CUDA
operator loading/building, distributed initialization, or filesystem setup.
Run `scripts/check_runtime.py` first; it is read-only and reports JSON.

## Workflow

1. Read [installation.md](references/installation.md) for historical version
   constraints and installation order.
2. Run the runtime diagnostic and separate framework CUDA availability from
   `nvcc`, compiler, extension, and `spconv` availability.
3. Read [custom-ops.md](references/custom-ops.md) before rebuilding any
   extension; match Python, torch, CUDA toolkit, compiler, and GPU ABI.
4. Check [runtime-diagnostics.md](references/runtime-diagnostics.md) for import
   classification and distributed environment checks.
5. Apply [troubleshooting.md](references/troubleshooting.md) and preserve the
   first actionable error.

Do not call a CPU import a successful GPU capability check. Do not repair a
user-owned environment by silently changing torch, setuptools, CUDA, or
compiled packages. Training/evaluation and data conversion remain separate
side-effectful workflows.
