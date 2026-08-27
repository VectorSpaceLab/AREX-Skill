# C API troubleshooting

## `get_include()` points to a directory without headers

**Symptom**: `qiskit.capi.get_include()` returns a path, but `qiskit.h` is missing.

**Cause**: the installation is incomplete or the active Python is not the intended Qiskit environment.

**Fix**: reinstall Qiskit in a clean environment and run the bundled `capi` smoke check.

## `get_lib()` points to a missing library

**Symptom**: `qiskit.capi.get_lib()` returns a path that does not exist.

**Cause**: the Rust-backed extension was not built or the wheel/install is corrupted.

**Fix**: reinstall from a wheel when possible, or rebuild from source with the supported Rust toolchain.

## `_accelerate` import failure

**Symptom**: `import qiskit` or `import qiskit.capi` fails before any C API calls.

**Cause**: Qiskit's compiled extension is missing, stale, or incompatible with the active Python.

**Fix**: do not debug downstream C code until the base Python package imports successfully. Rebuild or reinstall first.

## Direct linking behaves differently across systems

**Symptom**: a local build works but a distributed extension fails to load elsewhere.

**Cause**: direct linking against the package library can tie the extension to local package layout and ABI details.

**Fix**: treat direct linking as an expert-only path and document the exact runtime expectations for the downstream package.

## Rust or build-backend errors during source install

**Symptom**: source install fails before Qiskit can import.

**Cause**: missing Rust, unsupported toolchain, missing `setuptools-rust`, or a stale build cache.

**Fix**: create a fresh build environment, confirm the toolchain, and rebuild the package before using `qiskit.capi`.
