# JIT and tracing notes

## What the tests show

Asteroid has explicit JIT coverage for:

- model tracing on small waveform inputs
- filterbank/encoder-decoder helpers
- utility functions such as `jitable_shape`
- model blocks that depend on shape normalization

## Practical rules

- Normalize input shapes before tracing.
- Keep time-last conventions consistent.
- Prefer tiny synthetic inputs when checking traceability.
- Verify that traced and eager outputs agree on the same input tensor.

## Functions to remember

- `asteroid.utils.torch_utils.jitable_shape`
- `asteroid.utils.torch_utils.script_if_tracing`
- `asteroid.utils.torch_utils.pad_x_to_y`
- `asteroid.complex_nn.on_reim`
- `asteroid.complex_nn.ComplexSingleRNN`

## Typical failure modes

- shape mismatch after unsqueezing or stacking
- complex tensors being fed into a real-valued helper
- tracing a module that changes behavior based on the Python type of the input
- hidden assumptions about batch, channel, or time axes

## Good smoke cases

- `tests/jit/jit_models_test.py`
- `tests/jit/jit_filterbanks_test.py`
- `tests/jit/jit_masknn_test.py`
- `tests/jit/jit_torch_utils_test.py`
