# Troubleshooting

This file focuses on the deployment-exchange failure modes that are safe to diagnose from the prepared evidence set.

## NIR problems

### `TypeError: IF.__init__() got an unexpected keyword argument 'input_type'`

**Meaning**: The installed NIR release does not match the shape-bearing neuron constructor path used by the current `export_to_nir` implementation.

**What to do**

- Treat stateless graph round-tripping as the verified path in the prepared environment.
- Do **not** claim that neuron-node export/import is verified unless the NIR package matches the constructor contract used by `to_nir.py`.
- If the user needs full spiking-node exchange, verify the NIR release first and then retry.

### Exported graph has the wrong shapes

**Common causes**

- `example_input` did not match the real execution path.
- A module was not one of the supported NIR-export types.
- You expected batch or time axes to appear in the NIR graph.

**Fixes**

- Re-run export with an executable `example_input` that follows the same module path.
- Remember that NIR shape metadata is per-sample and per-time-step only.
- Check `Flatten` and the surrounding layers first if the inferred shapes look off.

### Imported model returns a tuple

**Meaning**: This is expected.

**Fix**: Use `output = result[0]` for the forward output and treat `result[1]` as the internal state dictionary.

## Lava problems

### `TNX_to_NXT` / `to_lava_neuron` / `BlockContainer` is missing

**Meaning**: The optional Lava-DL stack is not installed.

**Fix**: Keep the Lava path at the documentation level only, or install the optional Lava-DL dependencies before retrying.

### `ValueError: lava only supports for v_reset == 0`

**Meaning**: The conversion helper only supports hard reset at zero.

**Fix**: Reconfigure the neuron or route the model away from the Lava conversion helper.

### `ValueError: lava only supports for decay_input == False`

**Meaning**: The Lava LIF conversion path is narrower than the general SpikingJelly neuron.

**Fix**: Use the supported parameterization or keep the model in the SpikingJelly domain.

### Pooling does not match the ANN reference

**Meaning**: The Lava pooling helper returns sum pooling, not true average pooling.

**Fix**: Adjust the comparison or rescale the result in the caller.

### `Flatten` conversion fails

**Meaning**: The Lava block path expects `start_dim == 1`.

**Fix**: Rewrite the model or use a different deployment route.

## Lynxi problems

### `compile_lynxi_model` or `load_lynxi_model` is missing

**Meaning**: The optional vendor stack (`lyngor` / `lynpy`) is not installed.

**Fix**: Treat the Lynxi path as documentation-only until the runtime stack is available.

### Unsupported layer is silently copied or logged as critical

**Meaning**: `to_lynxi_supported_module(s)` only rewrites the supported subset.

**Fix**: Rewrite the model to use the supported module set before compiling.

### 5D tensor or in-place mutation errors

**Meaning**: Lynxi compilation does not tolerate 5D tensors anywhere in the graph, and in-place ops are disallowed.

**Fix**: Flatten `T` and `N` into `[TN, *]` when needed, and remove in-place writes.

### Shape mismatch after compilation

**Meaning**: The caller probably forgot the `T` contract or the sequence reshape contract.

**Fix**

- Ensure the model was rewritten with the correct `T`.
- Reshape sequence outputs back to `[T, N, *]` before reducing over time.
- When decoding vendor tensors, call `lynxi_tensor_to_torch(..., shape=..., dtype=...)` with both arguments together.

## When to escalate

Escalate out of this sub-skill when:

- the user needs backend profiling or kernel behavior comparisons,
- the user needs a training recipe or benchmark,
- the user is asking for ANN2SNN conversion semantics rather than deployment exchange,
- the requested deployment runtime is absent and they want installation help beyond the documented contract.
