# Framework Integration Troubleshooting

## `RuntimeError: Tensor type unknown to einops`

Likely causes:

- The tensor framework module was not imported before calling `einops`.
- The object is a wrapper type not recognized by the backend class.
- The backend is optional and not installed in this environment.
- The tensor follows Array API but the user used the top-level backend registry
  path instead of `einops.array_api`.

Recovery:

1. Import the framework explicitly before creating/passing tensors.
2. Print `type(tensor)` and confirm it is a native tensor class.
3. For Array API objects, try `from einops import array_api as E` and call
   `E.rearrange`/`E.reduce`/`E.repeat`.
4. Run `scripts/array_api_smoke.py` or a tiny framework operation before a full
   model refactor.

## Missing optional dependency when importing layer modules

Symptom examples:

```text
ModuleNotFoundError: No module named 'torch'
ModuleNotFoundError: No module named 'tensorflow'
ModuleNotFoundError: No module named 'flax'
```

Cause: `einops` does not install tensor frameworks. Layer modules import their
framework directly.

Recovery:

- Install only the framework the project already uses.
- Do not install all supported frameworks to fix one missing import.
- If a package manager resolves conflicting TensorFlow/Paddle/OneFlow stacks,
  split framework checks into separate environments.
- Use `scripts/layer_smoke.py --framework <name>` after installation.

## Array API smoke fails

Common causes:

- NumPy is older than 2.0 and lacks the exact Array API/DLPack behavior used by
  the repository tests.
- The provider does not implement `__array_namespace__` or `__dlpack__`.
- A reduction name exists in `einops` but not in the provider namespace.
- The provider's `concat`, `reshape`, `broadcast_to`, or slicing semantics
  differ from NumPy.

Recovery:

1. Confirm the object has `__array_namespace__`.
2. Run `scripts/array_api_smoke.py --framework numpy` or the relevant optional provider.
3. If `asnumpy` fails, avoid claiming DLPack conversion and validate shapes with
   provider-native inspection.
4. Use top-level `einops` for known backend tensor classes rather than forcing
   Array API mode.

## TensorFlow/Keras layer version confusion

Source comments state that layer construction changed often and the current
TensorFlow layer implementation follows TF 2.16-style instructions. If Keras
serialization or `build`/`call` behavior fails:

- Verify the TensorFlow version in the user's environment.
- Use `einops.layers.keras.keras_custom_objects` when loading saved Keras
  models.
- Start with `Rearrange` or `Reduce` before testing an `EinMix` layer.
- Compare a tiny eager call to expected top-level `einops` output.

## Torch scripting, tracing, and compile failures

Symptoms:

- Eager `Rearrange` works but `torch.jit.script` fails.
- `torch.compile` output differs from eager output.
- Dynamic shapes cause a compiled graph failure.

Recovery:

1. First verify the pattern in eager mode on a tiny tensor.
2. For model layers, use `einops.layers.torch.Rearrange`/`Reduce`; source uses a
   torch-specific scriptable recipe for these layers.
3. For top-level functions under `torch.compile`, ensure torch 2.x is used and
   compare eager vs compiled results on at least two shapes.
4. If using torch versions before 2.8, `einops._torch_specific` registers
   top-level ops with Dynamo when the torch backend is initialized.
5. Do not present a CPU compile smoke as CUDA runtime proof.

## EinMix axis and shape errors

Common symptoms and causes:

| Error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `Dimension ... of weight should be specified` | An axis in `weight_shape` lacks a length argument. | Add `axis=value` or Flax `sizes={...}`. |
| `Parenthesis is not allowed in weight shape` | `weight_shape` uses grouped axes. | List flat weight axes and use grouped axes in input/output pattern if needed. |
| `Ellipsis is not supported in weight` | Weight tensor shape must be fully specified. | Replace ellipsis with explicit axes. |
| `Ellipsis in EinMix should be on both sides` | Input/output pattern has ellipsis on only one side. | Preserve ellipsis on both sides or remove it from both. |
| `Ellipsis on left side can't be in parenthesis` | Input pattern parenthesizes ellipsis, e.g. `(...) a`. | Keep the left-side ellipsis ungrouped. |
| `Anonymous axes (numbers) are not allowed in EinMix` | Numeric anonymous axes appear in pattern or weight. | Name the axis and pass its size. |
| `Unrecognized identifiers on the right side` | Output axis is neither an input axis nor a weight axis. | Add the axis to input/weight or remove it from output. |
| `Bias axes ... not present in output` | Bias shape names axes absent from the right side. | Restrict bias to output axes. |
| `Sizes not provided for bias axes` | A bias axis is missing from supplied lengths. | Add the missing size argument or Flax `sizes` entry. |
| `Axes ... are not used in pattern` | Extra length arguments were supplied. | Remove unused axis lengths or include them in input/weight/output. |
| `Weight axes ... are redundant` | A weight axis participates in neither input nor output. | Remove the redundant axis or use it in the transformation. |

When debugging `EinMix`, instantiate the smallest possible layer and run the pure
helper checks with `scripts/layer_smoke.py --framework pure` before adding a full
framework dependency.

## Accelerator confusion

Because `einops` delegates to the framework, accelerator behavior follows the
framework tensor:

- If the input is a CPU tensor, the output is CPU.
- If the framework supports the operation on a CUDA/ROCm/MPS tensor, `einops`
  typically preserves that device.
- If the framework lacks a reduction or reshape behavior on the device, `einops`
  cannot fix it.

Recovery:

1. Verify framework device availability separately.
2. Create a tiny tensor directly on the target device.
3. Run one `rearrange` and one relevant `reduce`/`repeat` on that device.
4. Only then claim the user's accelerator path is verified.
