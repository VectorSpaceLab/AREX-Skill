# Installation and Build Troubleshooting

## Import and package identity

**Symptom:** `No module named tvm`.

- For a source checkout, prepend its `python/` directory to `PYTHONPATH`.
- Confirm the build included `TVM_BUILD_PYTHON_MODULE=ON`.
- Confirm `apache-tvm-ffi` is installed in the same Python environment.
- Run `check_tvm_install.py --json` and inspect `tvm_file`.

**Symptom:** TVM imports, but it is the wrong checkout.

- Print `tvm.__file__`, `tvm.__version__`, and `tvm.support.libinfo()`.
- Remove stale checkout entries from `PYTHONPATH` and avoid editable installs.
- Set `TVM_LIBRARY_PATH` to the intended build library directory while
  diagnosing, then use the normal packaging/discovery mechanism once fixed.

**Symptom:** `tvm-ffi` is missing or has an incompatible API.

- Install the package version required by the checkout's `pyproject.toml`.
- Re-run `python -m pip check`.
- Do not mix a wheel's Python package with a different checkout's runtime libs.

## CMake and linker failures

**Symptom:** CMake cannot find Ninja, C/C++ compilers, or LLVM.

- Check that `cmake`, `ninja`, a supported compiler, and `llvm-config` are on
  `PATH` (or pass an explicit LLVM configuration accepted by this checkout).
- Reconfigure after correcting the toolchain; changing `PATH` after CMake has
  cached a failed discovery may not be sufficient.

**Symptom:** `cannot find -lxml2`, `-lxml2` link failure, or LLVM link failure.

- Install the development package that supplies the unversioned `libxml2.so`
  link and headers, not only a runtime library.
- Ensure the linker search path contains that development prefix.
- Delete or refresh the affected build cache and rebuild.

**Symptom:** Python import succeeds but `libtvm` or `libtvm_runtime` cannot load.

- Inspect the loaded paths and `LD_LIBRARY_PATH`/platform equivalent.
- Verify that the build's dependent shared libraries are discoverable.
- Do not use a compiler library from one checkout with a runtime library from
  another.

## Backend and test failures

**Symptom:** CUDA is disabled despite an NVIDIA GPU being visible.

A driver and visible device are insufficient when the build lacks CUDA headers,
`nvcc`, or CUDA CMake support. Record CUDA as unverified, use the CPU/LLVM path,
or prepare a matching toolkit before enabling it.

**Symptom:** TIRx Blackwell tests skip or fail on an A100/older GPU.

The registry/codegen tests that require compute capability 10.0+ cannot be
validated on compute capability 8.0 hardware. Keep them optional or blocked as
specified by the verification plan; do not claim that parser/layout CPU tests
prove Blackwell execution.

**Symptom:** An optional dependency import fails.

Install only the relevant extra: `meta-schedule` for XGBoost-backed tuning,
`rpc`/`popen-pool` for process and RPC workflows, `torch` for Torch examples,
or `cuda` for CUDA Python helpers. Route to a CPU-only workflow when that is
sufficient.

## Safe recovery order

1. Capture `python`, package, source commit, and build option facts.
2. Fix environment/toolchain discovery.
3. Reconfigure and rebuild.
4. Re-run import/library diagnostics.
5. Run one focused native test.
6. Broaden only if the focused check passes.
