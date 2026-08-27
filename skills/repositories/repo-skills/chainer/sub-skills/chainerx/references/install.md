# ChainerX Install and Build

ChainerX is optional. A normal Chainer install can include an importable `chainerx` package while still reporting `chainerx.is_available() == False`.
That means the C++ core was not built.

## Source build variables

Set build flags before installing from source:

```bash
export CHAINER_BUILD_CHAINERX=1
export MAKEFLAGS=-j8
pip install chainer
```

Important variables:

| Variable | Purpose |
| --- | --- |
| `CHAINER_BUILD_CHAINERX` | `1` to build ChainerX, `0` to skip. Default is `0`. |
| `CHAINERX_BUILD_CUDA` | `1` to build CUDA support. Default is `0`. |
| `CHAINERX_ENABLE_BLAS` | `1` to use BLAS if found. |
| `CHAINERX_ENABLE_LAPACK` | `1` to use LAPACK if found. |
| `CHAINERX_CMAKE_GENERATOR` | `ninja` to use Ninja. |
| `CHAINERX_BUILD_TYPE` | Override the CMake build type. |

## CUDA support

For CUDA support, ChainerX also needs cuDNN information.
Use one of:

```bash
export CHAINERX_BUILD_CUDA=1
export CHAINERX_CUDNN_USE_CUPY=1
```

or:

```bash
export CHAINERX_BUILD_CUDA=1
export CUDNN_ROOT_DIR=/path/to/cudnn
```

The CUDA fallback path expects CuPy to be installed with a CUDA-compatible wheel or source build.

## Build requirements

The source helper checks for:

- CMake >= 3.1.0
- a supported C++ compiler
- optional Ninja when requested
- Python >= 3.5 for ChainerX

## After build

Run:

```bash
python - <<'PY'
import chainerx
print(chainerx.is_available())
PY
```

Then run `../../scripts/chainerx_probe.py` to test a tiny array operation.
