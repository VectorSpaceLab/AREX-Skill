---
name: custom-op-console-and-tools
description: "Use advanced Jittor extension APIs for custom operators, jt.code
  kernels, C++ console embedding, and safe utility or converter workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Custom op, console, and tools

Use this sub-skill when a task asks for advanced Jittor extension surfaces: inline `jt.code`, compiled custom ops, meta-operator design, C++ console embedding, utility CLI flags, or bounded PyTorch conversion/interoperability notes.

Do not use it for ordinary model/layer training, package installation, CUDA toolkit setup, dataset/model zoo workflows, or low-level framework internals that are not exposed by the public APIs. Route those tasks to the appropriate sibling sub-skill.

## Read and run map

| Need | Use |
| --- | --- |
| Decide between meta-operators, `jt.code`, `compile_custom_op`, and `compile_custom_ops` | Read [references/custom-op-and-code.md](references/custom-op-and-code.md). |
| Write or review a CPU-first custom code-op smoke check | Run [scripts/custom_op_smoke.py](scripts/custom_op_smoke.py) with `--help`, then `--skip-compile` or the default tiny CPU smoke. |
| Generate C++ console compile flags, example source, or a compile command template | Read [references/console-and-utilities.md](references/console-and-utilities.md) and run [scripts/jittor_console_flags.py](scripts/jittor_console_flags.py). |
| Diagnose compiler, shape, dtype, CUDA, console-link, converter, or unsafe-service failures | Read [references/troubleshooting.md](references/troubleshooting.md). |

## Default operating workflow

1. Confirm the user really needs an extension surface. Prefer meta-operators for shape-indexing algebra, `jt.code` for small inline C++/CUDA kernels, and `compile_custom_op(s)` only for larger op classes or multi-file C++/CUDA implementations.
2. Verify a CPU path first. A CUDA kernel, CUDA branch in a custom op, or CUDA-only `jt.code` snippet is a separate optional verification step and must be guarded by CUDA availability.
3. Keep shape and dtype contracts explicit. Record output shapes/dtypes before writing source strings; verify with tiny arrays and synchronized values before scaling.
4. For C++ console embedding, use `jittor_utils.config` through the bundled wrapper to generate flags or example code. Do not assume the host has a linkable Python shared library or a C++17-capable compiler.
5. Treat converter and service utilities as boundary tools. Text conversion still requires manual review and tests; service/server scripts are not safe defaults.

## Safety gates

- Do not start long-running converter services, Docker containers, network listeners, or network downloads unless the user explicitly requests that service work and accepts the boundary.
- Do not claim CUDA verification from a CPU run. Use optional CUDA probes only when the runtime backend is available and intentionally selected.
- Do not paste local include, library, cache, or checkout paths into generated guidance. CLI wrappers may print user-local flags at run time because those are compile inputs, but reference material should stay path-agnostic.
