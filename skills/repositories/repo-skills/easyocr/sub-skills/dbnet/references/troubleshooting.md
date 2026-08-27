# EasyOCR DBNet Troubleshooting

Use this page when DBNet or the DCN operator does not start cleanly.

## Detector selection errors

### Unsupported detector network

The current `Reader` surface only accepts `craft` or `dbnet18` as detector
choices. If you see an unsupported-network error, double-check the spelling and
avoid assuming `dbnet50` is a public `Reader` option in this checkout.

## Import and initialization issues

### DBNet import succeeds but initialization fails

Try the lazy CPU smoke first:

```python
from easyocr.DBNet.DBNet import DBNet
DBNet(initialize_model=False, device='cpu', verbose=0)
```

If that works, the failure is likely in the detector weights or the selected
device, not in the module import itself.

### Device mismatch error

DBNet expects the device used at initialization and the device used at runtime
to match. Recreate the object with the same device string and try again.

## DCN compilation issues

### Missing shared objects

If the expected `deform_conv_*` or `deform_pool_*` shared objects are missing,
run `scripts/compile_dcn.py --build` again after checking compiler
prerequisites.

### Missing GCC or NVCC

- CPU builds need a modern GCC toolchain.
- CUDA builds need the same GCC baseline plus a CUDA toolkit/NVCC install.

If the host has a CUDA-enabled torch wheel but no `nvcc`, the current DBNet
setup script still tries to compile CUDA extensions and will fail. Install the
CUDA toolkit/NVCC or switch to a CPU-only torch wheel before rebuilding.

If the host lacks the required toolchain, fix the environment first and then
rebuild.

## Runtime backend quirks

### CPU fallback confusion

The DBNet package can be inspected on CPU even when the full detector run is
intended for CUDA. Make sure the verification step matches the user's actual
backend requirement.

### Incomplete build artifacts

If one of the two expected CPU or CUDA shared libraries is missing, rerun the
helper after confirming the host backend and compiler support.

## Best first step

Run `scripts/compile_dcn.py --check-only` before assuming a full rebuild is
needed. It tells you whether the operator is already present.
