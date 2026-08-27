# torchsummary Usage Troubleshooting

This reference covers failures that usually occur while calling
`torchsummary.summary` or `torchsummary.summary_string`. For package-wide
install/import/backend issues shared with other sub-skills, see the root shared
troubleshooting reference: [../../../references/troubleshooting.md](../../../references/troubleshooting.md).

## Symptom-to-fix guide

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` or `No module named 'numpy'` | `torchsummary` version `1.5.1` imports both packages, but its package metadata does not declare them as install requirements. | Install `torch` and `numpy` in the active runtime, then retry the import check in [workflows](workflows.md). |
| CUDA error on a CPU-only host, often mentioning CUDA initialization or unavailable driver | The default `device` is `torch.device("cuda:0")`. | Pass `device="cpu"` or `torch.device("cpu")`, and move the model to CPU before calling `summary`. |
| `Expected all tensors to be on the same device` | Generated synthetic inputs are on the `device` argument, but model parameters or buffers are elsewhere. | Use one device object and apply it to both: `model = model.to(device)` and `summary(..., device=device)`. |
| `forward() missing ... positional argument` for a multiple-input model | `input_size` was passed as one tuple or has too few entries. | Use a list of tuples, one per positional input: `input_size=[(1, 300), (1, 300)]`. |
| Error from `torch.rand` or tuple expansion when using multiple inputs | Multiple inputs were written as a tuple of tuples. The implementation treats any tuple as a single input. | Use a Python list of tuples, not `((...), (...))`. |
| `mat1 and mat2 shapes cannot be multiplied`, convolution shape errors, or invalid `view`/`reshape` | `input_size` does not match the model's expected non-batch input shape. | Remove the batch dimension and match the shape consumed by `forward`. For CNNs, use `(channels, height, width)`. For vector models, use the feature shape expected by the model. |
| Dtype mismatch, for example a long tensor reaching `nn.Linear` | `dtypes` generated an integer input but the model branch expects floating-point operations. | Align `dtypes` with `forward` arguments and convert integer branches inside the model before floating-point layers. |
| Device mismatch after converting a dtype branch | Code such as `x.type(torch.FloatTensor)` converts to a CPU tensor class. | Prefer `x.to(device=reference.device, dtype=torch.float32)` for device-safe conversion. |
| Returned parameter counts fail strict `isinstance(value, int)` checks | Modern PyTorch may return scalar tensor counts from `torch.prod`. | Compare with `int(value.item()) if hasattr(value, "item") else int(value)`. |
| Unexpected 0-parameter row for the model or wrapper module | Forward hooks can fire on custom root/wrapper modules in newer PyTorch. | Treat the row as a display artifact if totals from parameter-owning modules are correct; use `torchinfo` for cleaner modern formatting. |
| Reused layer appears more than once | Hooks fire per forward call. A shared module used twice can produce two rows. | Interpret rows as forward executions. Check totals carefully for models with shared parameters. Prefer `torchinfo` or a custom audit if unique-parameter accounting matters. |
| Memory estimates look wrong or negative-looking batch dimensions appear in shapes | Default `batch_size=-1` is a display convention, and memory estimates are rough absolute 4-byte calculations. | Pass a display `batch_size` if desired, but use a profiler for real memory planning. |
| Model behaves differently during summary because of dropout or batchnorm | `torchsummary` runs a real forward pass and does not force eval mode. | Call `model.eval()` before summary when deterministic inference-mode behavior is wanted. |
| Model requires keyword-only arguments, dictionaries, masks, labels, or non-tensor metadata | `torchsummary` only creates positional synthetic tensors from `input_size`. | Wrap the model with a small `nn.Module` that supplies constants, or prefer `torchinfo`/custom inspection with real example inputs. |
| Model returns dictionaries or deeply nested structures | The implementation handles tensor outputs and simple list/tuple outputs best. | Use `summary_string` only if the model output structure is supported; otherwise prefer `torchinfo` or a custom forward probe. |
| Failure leaves later summaries with duplicated rows | If a forward pass raises before hooks are removed, hooks may remain on that model instance. | Recreate the model instance or run the next summary in a fresh process after a failed summary call. |
| Large VGG/torchvision-style example is slow or runs out of memory | Large models and optional `torchvision` examples are not part of the minimum package workflow. | Validate with the bundled smoke helper first; use smaller input sizes or `torchinfo` for larger modern models. |

## CPU-safe correction pattern

Use this correction whenever the failure mentions CUDA on a CPU-only host or
mixed devices:

```python
import torch
from torchsummary import summary

device = torch.device("cpu")
model = model.to(device)
summary(model, input_size=(1, 28, 28), device=device)
```

If CUDA is available and desired:

```python
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = model.to(device)
summary(model, input_size=(1, 28, 28), device=device)
```

## Multiple-input correction pattern

Wrong for two inputs:

```python
summary(model, input_size=((1, 300), (1, 300)), device="cpu")
```

Correct:

```python
summary(model, input_size=[(1, 300), (1, 300)], device="cpu")
```

With per-input dtypes:

```python
import torch

summary(
    model,
    input_size=[(1, 300), (1, 300)],
    device="cpu",
    dtypes=[torch.FloatTensor, torch.LongTensor],
)
```

## Shape-debug checklist

1. Remove the batch dimension from every `input_size` tuple.
2. Verify the synthetic shape that will be created: `(2, *input_size_tuple)`.
3. Check that the model's first layers accept that shape.
4. For flatten/view layers, recompute the feature count after convolutions or
   pooling.
5. For multiple inputs, verify the list length and order match the `forward`
   positional arguments.
6. If the model's `forward` needs non-tensor data, wrap the model or use a tool
   that accepts real sample inputs.

## Count-debug checklist

1. Normalize counts to integers before comparing.
2. Confirm that parameters are attached to modules with `weight` and/or `bias`
   attributes.
3. Remember that non-trainable counts are computed as `total - trainable`.
4. Expect possible 0-parameter rows for wrappers or activations.
5. Be cautious with reused modules: rows are hook calls, while parameter totals
   should be interpreted in the context of shared-parameter model design.

## Smoke helper

Run the bundled helper from the sub-skill directory to distinguish
package/runtime failures from issues in a user model:

```bash
python scripts/smoke_summary.py --case all --device cpu
```

If your current directory is this `references/` directory, use:

```bash
python ../scripts/smoke_summary.py --case all --device cpu
```

The helper asserts deterministic expected parameter counts for single-input,
multiple-input, and per-input dtype cases.
