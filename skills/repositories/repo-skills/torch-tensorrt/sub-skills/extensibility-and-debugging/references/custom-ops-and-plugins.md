# Custom Converters, Lowerings, and Plugins

## When a custom extension is warranted

Write a custom extension only when all of these are true:

- The op is important to the user's workload.
- Fallback is too slow or too expensive.
- A model rewrite is not practical or would be too invasive.
- The op's semantics are stable enough to encode into a converter or plugin.
- The target TensorRT version actually supports the extension mechanism you need.

## Path comparison

| Path | Best for | Trade-off |
| --- | --- | --- |
| Model rewrite/decomposition | Small, local unsupported-ops fix | Fastest if the model can be expressed using supported ops. |
| Custom converter | Known ATen/TorchScript-to-TRT mapping | Requires working with conversion context and TensorRT layers. |
| TensorRT plugin | Backend-native op or fused kernel | More work, but can be efficient and reusable. |
| QDP kernel | User-defined CUDA kernel with Torch-TensorRT integration | Useful for advanced plugin-like custom kernels; requires CUDA/kernel authoring. |

## Converter checklist

A useful converter note or issue should include:

- exact op schema,
- example inputs and shapes,
- dtype/layout/device,
- whether the op appears in Dynamo or TorchScript path,
- whether the op can be decomposed from other supported ATen ops,
- whether a backend plugin already exists,
- how the op should behave under fallback or `require_full_compilation`.

## Plugin checklist

- Verify TensorRT version support and plugin package availability.
- Verify whether the plugin is for standard TensorRT or TensorRT-RTX.
- Confirm serialization and runtime loading behavior in the target environment.
- Ensure the plugin does not depend on hidden source-checkout paths or ad hoc build side effects.

## Example strategy for a custom converter request

1. Reproduce the unsupported op on a minimal model.
2. Confirm the op schema and input constraints.
3. Decide whether decomposition is possible.
4. If not, sketch a converter that creates the TensorRT layers and associates the output tensors.
5. Validate with a tiny compile smoke and only then scale up.
