# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: nir` or `ModuleNotFoundError: nirtorch` | The active environment is missing the NIR dependencies. | Install and verify both packages before retrying export or import. |
| Type inference fails during export or `nir.read` | `sample_data` does not match the live forward path, or the graph / fixture is stale relative to the current NIR library. | Use a representative sample tensor, keep `ignore_dims=[0]` for batched inputs, and rebuild stale fixtures if needed. |
| `ValueError: V must be a vector, cannot infer layer size for scalar V` | `RLeaky` or `RSynaptic` is using `all_to_all=False` with a scalar recurrent `V`. | Provide a vector `V` with one value per neuron, or switch to the dense recurrent path. |
| `TypeError: 'int' object is not iterable` inside `AvgPool2d` import | The exported pool node stored scalar `kernel_size` or `stride` values. | Rebuild the model with tuple-valued pool args before exporting. |
| The recurrent block is not collapsed back into one module | The graph has extra edges or does not match the simple recurrent cycle. | Keep the recurrent subgraph as one `lif` / `w_rec` cycle with the expected input and output edges. |
| The imported call returns a tuple | The executor returns the output tensor plus state. | Use the first tuple item for shape checks and comparisons. |
| Output shapes do not match the original model | `ignore_dims` was omitted or the traced sample tensor had the wrong rank. | For batch-first models, use `ignore_dims=[0]` and make `sample_data` match the real input shape. |
| Vectorized `beta`, `alpha`, or `threshold` sizes do not match the hidden width | Per-neuron parameters were created with the wrong length. | Make each vector length match the neuron count for that layer. |

## Current conv/pool note

The bundled conv/pool compatibility fixture is preserved for debugging the current edge case. It is not a guarantee that every `AvgPool2d` graph will import cleanly; the safest path is a tuple-valued pool configuration with a matching traced shape.
