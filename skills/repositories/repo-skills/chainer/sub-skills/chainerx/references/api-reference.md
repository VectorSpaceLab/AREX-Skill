# ChainerX API Reference

## Availability

- `chainerx.is_available()` returns whether the ChainerX C++ core is built and importable.
- When unavailable, `chainerx.ndarray` exists only as a dummy class for type testing and raises at construction time.

## Arrays

- `chainerx.ndarray` is the ChainerX array type.
- `chainerx.array(...)`, `ones(...)`, `ones_like(...)`, and random helpers create arrays when ChainerX is available.
- `chainerx.to_numpy(...)` converts ChainerX arrays to NumPy.
- `ndarray.require_grad()` marks an array for automatic differentiation.
- `ndarray.backward()` performs backpropagation through the ChainerX graph.
- `ndarray.to_device(...)` moves an array to another ChainerX device.

## Backends and devices

- `chainerx.get_backend(...)`
- `chainerx.get_device(...)`
- `chainerx.get_default_device()`
- `chainerx.set_default_device(...)`
- `chainerx.using_device(...)`

Device names use `<backend>:<index>` style strings, for example:

- `native:0` for the CPU native backend
- `cuda:0` for the first CUDA backend device

## Chainer integration

Chainer can wrap a ChainerX array in `chainer.Variable`.
When Chainer functions run on variables backed by ChainerX arrays, the computation graph is recorded in ChainerX.
Fallback converts to NumPy or CuPy for functions that do not have direct ChainerX implementations.

Useful Chainer-side helpers:

- `chainer.backend.get_device('native:0')`
- `chainer.backend.get_device('cuda:0')`
- `chainer.backend.to_chx(...)`
- `chainer.backend.from_chx(...)`
- `chainer.Link.to_device(...)`

## Limitations to remember

- Supported dtypes are limited to bool, signed integers, unsigned int8, float32, and float64 families documented by ChainerX.
- Mixed dtype operations are not supported; cast explicitly.
- True division with integer arrays is not NumPy-identical.
- Only a limited set of Chainer functions is well-tested with ChainerX integration.
- CUDA backend requires cuDNN.
- In-place writes on grad-tracked arrays are restricted for safety.
