# C API build and link notes

## 1. Locate headers and library from Python

```python
import qiskit.capi

include_dir = qiskit.capi.get_include()
lib_path = qiskit.capi.get_lib()
```

Use `get_include()` for the directory containing `qiskit.h` and the auxiliary `qiskit/*.h` headers. Use `get_lib()` to find the shared-object file that contains the exported C-API symbols.

## 2. Inspect ctypes bindings

`qiskit.capi` re-exports typed ctypes wrappers for the public C API. The ctypes object names follow the C API names, such as `qk_*` functions and enum/struct names.

## 3. Build from source when needed

For a source checkout, Qiskit builds a Rust-backed extension. The source-tree build commands documented by the repository include:

```bash
python setup.py build_rust --inplace --release
make c
```

Treat those commands as source-tree operations, not runtime operations for this skill.

Useful build facts from the source metadata:

- Rust toolchain support is required for source builds.
- The Python build backend uses `setuptools` and `setuptools-rust`.
- Build profile behavior can be influenced by environment variables such as `QISKIT_BUILD_PROFILE`, `QISKIT_NO_CACHE_GATES`, and `QISKIT_BUILD_WITH_MIMALLOC`.

## 4. Direct-link caveat

The package API explicitly warns that direct linking against the object returned by `get_lib()` is not generally a safe way to build a distributable Python extension module. Use it for local inspection or consciously controlled builds, and prefer supported extension patterns for reusable packages.
