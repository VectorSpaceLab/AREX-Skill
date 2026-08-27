# Installation and build boundary

## Python package

The public distribution is `hnswlib`; the import is also `hnswlib`. Prefer a
compatible wheel when available:

```bash
python -m pip install hnswlib
python -c "import hnswlib, numpy; print(hnswlib.Index('l2', 2))"
```

A source install uses the repository's PEP 517 build configuration and compiles
the `hnswlib` extension from `python_bindings/bindings.cpp` and the public
headers. The build dependencies are `setuptools`, `wheel`, `numpy`, and
`pybind11`; runtime installation declares NumPy. Use an isolated environment
and install build tools before retrying a source build:

```bash
python -m pip install numpy pybind11 setuptools wheel
python -m pip install hnswlib
```

The extension selects C++14 when the compiler supports it and otherwise accepts
C++11. Unix builds normally use `-O3`, `-fopenmp`, `-pthread`, and
`-march=native` when supported. Set `HNSWLIB_NO_NATIVE=1` for a portable source
build when `-march=native` is rejected or the artifact will run on CPUs other
than the build host. On macOS the build uses libc++ and a deployment target;
MSVC uses `/EHsc`, `/openmp`, and `/O2`. Do not copy a compiler flag blindly
across toolchains.

## C++ header-only use

The C++ library has no hnswlib binary to link. Keep an include root whose child
is `hnswlib/`, include `<hnswlib/hnswlib.h>`, and compile as C++11 or newer:

```bash
c++ -std=c++11 -O2 -pthread -I"${HNSWLIB_INCLUDE}" app.cpp -o app
```

The bundled smoke wrapper requires an explicit `--include-dir`; this prevents
it from depending on a particular checkout layout. A CMake consumer can use the
exported interface target `hnswlib::hnswlib` after installing the headers and
CMake package configuration. OpenMP is used by the Python build and by some
repository examples, but ordinary header-only clients should select only the
thread/compiler flags their own platform requires.

## Validation boundary

After installation, verify from the intended environment rather than from a
source checkout that happens to shadow the import:

```bash
python -m pip check
python -I -c "import hnswlib, numpy; print(hnswlib.Index('l2', 2))"
```

Then run a tiny add/query smoke. A successful import alone does not prove that a
source build's compiler flags, persistence, filtering, or vector shape contract
work.

## What is not part of installation

This release has no CUDA/ROCm/MPS dependency or GPU API. NVIDIA hardware does
not change the package install path. The BigANN/SIFT benchmark requires separate
large data and is intentionally not a setup smoke test. Java, R, and other
implementations mentioned in public documentation are external projects, not
installed by this skill.
