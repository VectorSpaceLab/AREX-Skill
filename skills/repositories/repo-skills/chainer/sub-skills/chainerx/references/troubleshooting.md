# ChainerX Troubleshooting

## `chainerx.is_available()` is false

Likely cause:

- Chainer was installed without `CHAINER_BUILD_CHAINERX=1`.

Recovery:

- Rebuild from source with ChainerX enabled.
- Confirm the build produced the ChainerX C++ core.
- Run `../../scripts/chainerx_probe.py` after installation.

## `_build_info.py` or `_core` cannot be imported

Likely causes:

- The source tree is being imported directly instead of the installed package.
- The package was installed in non-editable mode but Python is resolving the source checkout.
- The ChainerX build did not complete.

Recovery:

- Inspect `python -c 'import chainerx, inspect; print(chainerx.__file__)'`.
- Reinstall from a clean source checkout.
- Avoid mixing source checkout paths with installed site-packages.

## CUDA backend is missing

Likely causes:

- `CHAINERX_BUILD_CUDA=1` was not set.
- cuDNN was not located during build.
- CuPy was not installed when using the CuPy fallback path.

Recovery:

- Install a CUDA-compatible CuPy wheel.
- Set `CHAINERX_CUDNN_USE_CUPY=1` when cuDNN comes from the CuPy wheel.
- Or set `CUDNN_ROOT_DIR` explicitly.

## In-place update fails

ChainerX prohibits some in-place updates on arrays that participate in a computational graph.
Use `as_grad_stopped()` only when you are certain the mutation will not invalidate gradients.

## Mixed dtype operation fails

ChainerX does not support mixed dtype operations.
Cast explicitly with `astype(...)` or Chainer's `F.cast(...)`.

## Static graph optimization conflicts

Chainer's static graph optimization is not supported with ChainerX.
Set `chainer.config.use_static_graph = False` when using ChainerX-backed models.

## GPU memory usage is too high with CuPy

ChainerX and CuPy maintain separate memory pools by default.
Set `CHAINERX_CUDA_CUPY_SHARE_ALLOCATOR=1` before allocations if you need the experimental shared allocator behavior.
