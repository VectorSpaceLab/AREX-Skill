# Troubleshooting

## Purpose

Use this when TVM import, build, codegen, backend, or RPC workflows fail.
This is the cross-cutting place for issues shared across install/build,
Relax compilation, TIRx kernels, S-TIR tuning, and RPC deployment. Each
sub-skill should link here for shared failure modes and add its own workflow-
specific troubleshooting when needed.

## Common failures

### `ModuleNotFoundError: No module named 'tvm'`

Likely causes:
- The checkout's `python/` directory is not on `PYTHONPATH` for a source-style
  inspection.
- The runtime library path does not point at the built `build/lib` artifacts.
- The shell is importing a different TVM checkout or stale site-packages entry.

Recovery:
1. Run [`scripts/check_tvm_runtime.py`](../scripts/check_tvm_runtime.py) with
   `--repo-root` and, if needed, `--tvm-library-path`.
2. Confirm the Python process imports from the intended checkout and that
   `tvm.support.libinfo()` reports the expected commit and options.
3. Remove or deprioritize stale `PYTHONPATH` entries and confirm the build
   directory exists.

### TVM imports but runtime libraries are wrong or missing

Symptoms:
- Import succeeds, but the loaded runtime/compiler path points at a different
  checkout or an unexpected library.
- `tvm.base._LOADED_LIBS` does not include the expected build artifacts.
- `tvm.runtime.enabled("llvm")` or `tvm.cuda().exist` disagrees with the build
  plan.

Recovery:
- Rebuild the source checkout and set `TVM_LIBRARY_PATH` to the current
  `build/lib` directory while debugging.
- Use the repository-provided `PYTHONPATH` source-style import rather than
  editable installs.
- Re-run the runtime probe and inspect the loaded library paths.

### `-lxml2` / `libxml2` link failure during CMake or build

Symptoms:
- Linker errors mentioning `-lxml2`, `cannot find -lxml2`, or xml2 not found.
- CMake reports LLVM system libs including `-lxml2`.

Likely cause:
- The linker's library search path does not include the prefix that holds the
  unversioned `libxml2.so` symlink.

Recovery:
- Ensure the build prefix or environment exposes the shared library search
  path used by the linker.
- If the private prefix is missing the unversioned symlink, install the
  development package that provides it and rebuild.
- Re-run the CMake configure/build commands after the fix.

### LLVM / CMake / Ninja toolchain failures

Symptoms:
- CMake cannot find Ninja, a C/C++ compiler, or LLVM.
- `USE_LLVM` points at a prefix without a matching `llvm-config`.
- The build stops while linking `libtvm_compiler.so` or `libtvm_runtime.so`.

Recovery:
- Confirm the build prefix contains `cmake`, `ninja`, `git`, `llvm-config`,
  and a C++20-capable compiler.
- Reconfigure from a clean `build/` directory after the toolchain is fixed.
- If LLVM is not required for the selected workflow, narrow the scope before
  removing it from the generated guidance.

### Optional dependency missing

Symptoms:
- `xgboost` import fails during meta-schedule tasks.
- `tornado`, `psutil`, or `cloudpickle` are missing during RPC workflows.
- `torch` or `cuda-bindings` are missing for GPU-only examples or optional CUDA
  helper code.

Recovery:
- Install the dependency group that matches the selected workflow, not all
  extras.
- If the workflow does not require the optional capability, route the user to a
  CPU-only or alternative path and mark the backend as unverified rather than
  failed.

### GPU/backend mismatch

Symptoms:
- CUDA tests are skipped or fail because the host has no compatible toolkit,
  driver, or compute capability.
- TIRx Blackwell tests require compute capability 10.0+, but the host is an
  A100-class GPU or a CPU-only environment.
- `tvm.cuda().exist` is false even though the host has a visible NVIDIA GPU.

Recovery:
- Distinguish compile-time support from runtime device readiness.
- For optional CUDA guidance, document the missing toolkit/driver/backend and do
  not claim runtime coverage.
- For Blackwell-only TIRx kernels, keep the limitation explicit and use a
  compatible GPU before attempting final verification.

### RPC tracker/server/proxy issues

Symptoms:
- Connection refused, timeouts, wrong key, or tracker lookup failure.
- Remote module loads, but device execution times out or no devices are
  registered.

Recovery:
- Check the host/port/key arguments and the tracker registration order.
- Validate that the remote target and the exported module target match.
- Use the RPC help probe or targeted runtime test before starting a long-lived
  service.

## Next-step helpers

- `scripts/check_tvm_runtime.py` for import and backend readiness.
- `sub-skills/install-build/scripts/check_tvm_install.py` for source-build and
  import-path issues.
- `sub-skills/tirx-kernels/scripts/tirx_layout_probe.py` for layout and verifier
  checks.
- `sub-skills/s-tir-tuning/scripts/meta_schedule_import_probe.py` for optional
  dependency and API import checks.
- `sub-skills/rpc-deployment/scripts/rpc_cli_help_probe.py` for safe CLI help
  validation.
