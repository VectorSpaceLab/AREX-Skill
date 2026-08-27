---
name: c-api
description: "Guides agents locating Qiskit C headers and library, using
  qiskit.capi ctypes bindings, and handling public C-API build/link issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qiskit C API workflows

Use this sub-skill when the task involves Qiskit's public C API from Python: locating headers, locating the shared library, using ctypes bindings, planning downstream extension builds, or diagnosing source-build/link failures.

## Read next

- `references/build-and-link.md` for `qiskit.capi.get_include()`, `get_lib()`, ctypes access, and source-build notes.
- `references/troubleshooting.md` for missing headers/library, Rust extension, stale editable install, and direct-link caveats.
- `../../references/installation.md` for source-build prerequisites.
- `../../scripts/check_qiskit_environment.py --sections capi` for a source-free C-API path check.

## Include here

- `qiskit.capi.get_include()` and `qiskit.capi.get_lib()`.
- Python-space ctypes bindings exposed under `qiskit.capi`.
- Downstream C-extension or standalone C-library build planning that uses Qiskit's public headers.
- Source-build environment variables and Rust-backed extension diagnostics.

## Exclude or route elsewhere

- Python circuit construction belongs in `../circuit/SKILL.md`.
- Python transpilation APIs belong in `../transpiler/SKILL.md`.
- Backend/provider abstractions belong in `../providers/SKILL.md`.
- Generic C or Rust build-system advice not involving Qiskit belongs to a broader build-system skill.

## Default route

Start here when the user mentions `qiskit.capi`, `get_include`, `get_lib`, `qiskit.h`, `libqiskit`, ctypes wrappers, C extension modules, `make c`, Rust build failures, or missing `_accelerate` during a Qiskit source install.

## What to remember

- The Python package contains the public C headers and the shared-object library that backs the C API.
- `get_lib()` is useful for local introspection, but direct linking is not the safest path for distributable Python extensions unless the user understands the ABI caveats.
- Source builds require the supported Rust toolchain and the package build backend; normal wheels should already contain the built extension.
