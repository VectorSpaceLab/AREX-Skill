# Install and Optional Backends

Chainer 7.8.1 is a maintenance-phase deep learning framework.
The public docs describe support for Python 3.5.2+, 3.6.0+, 3.7.0+, and 3.8.0+ on Linux, with `pip install chainer` as the normal install path.

## Base install

```bash
pip install chainer
```

The project docs recommend upgrading `pip` and `setuptools` before installation when you control the environment.

## Common optional packages

- `cupy-cudaXX` or `cupy` `>=7.7.0,<8.0.0` for CUDA and cuDNN support.
- `pillow` `>=2.3` for image dataset support.
- `h5py` `>=2.5` for HDF5 serialization.
- `onnx<1.7.0` for ONNX-Chainer export.
- `mpi4py` plus a working MPI runtime for ChainerMN.
- `ideep4py` `>=2.0.0.post3,<2.1` for iDeep / Intel64 support.

## ChainerX source build knobs

ChainerX is not part of the default wheel install. The source build path uses environment variables before `pip install chainer` or `python setup.py ...`:

- `CHAINER_BUILD_CHAINERX=1` to include the `chainerx` package.
- `CHAINERX_BUILD_CUDA=1` to build CUDA support for ChainerX.
- `CHAINERX_CUDNN_USE_CUPY=1` or `CUDNN_ROOT_DIR=...` to locate cuDNN.
- `CHAINERX_ENABLE_BLAS=1` and `CHAINERX_ENABLE_LAPACK=1` to enable linear algebra backends when available.
- `CHAINERX_CMAKE_GENERATOR=ninja` to prefer Ninja when building.

## ChainerMN runtime knobs

- CPU-only ChainerMN can use the `naive` communicator without CuPy.
- GPU ChainerMN typically needs CuPy, NCCL, and CUDA-aware MPI.
- `mpi4py` is still required for communicator creation.

## Useful sanity check

```bash
python - <<'PY'
import chainer
print(chainer.__version__)
print(chainer.backends.cuda.available)
print(chainer.backends.cuda.cudnn_enabled)
PY
```
