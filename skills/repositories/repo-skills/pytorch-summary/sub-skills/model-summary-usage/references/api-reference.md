# torchsummary API Reference

This reference covers the public `torchsummary` API used by this generated
sub-skill. It is self-contained and does not require the original repository
checkout.

## Package and dependency facts

- Distribution name: `torchsummary`.
- Version evidenced for this skill: `1.5.1`.
- Import module: `torchsummary`.
- Public exports:

  ```python
  from torchsummary import summary, summary_string
  ```

- The package metadata does not declare `torch` or `numpy` as install
  requirements, but the implementation imports both. If either import is
  missing, install it in the active runtime before using this skill.

## Public signatures

The inspected public signatures are:

```python
summary(model, input_size, batch_size=-1, device=torch.device("cuda:0"), dtypes=None)
summary_string(model, input_size, batch_size=-1, device=torch.device("cuda:0"), dtypes=None)
```

Parameters:

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `model` | A PyTorch `torch.nn.Module`. | Move it to the same device that you pass as `device`; `torchsummary` does not move the model for you. |
| `input_size` | Shape(s) for synthetic inputs, excluding batch. | Use a tuple for one input, for example `(1, 28, 28)`. Use a list of tuples for multiple inputs, for example `[(1, 300), (1, 300)]`. |
| `batch_size` | Display/estimate batch dimension. | Default `-1` prints shapes like `[-1, ...]`. This does not change the internal synthetic forward batch size, which is always `2`. |
| `device` | Device for generated synthetic inputs. | Default is `cuda:0`. CPU-only code should pass `device="cpu"` or `torch.device("cpu")`. |
| `dtypes` | Optional list of tensor classes for generated inputs. | List order must align with `input_size`. Defaults to floating tensors. Multiple-input examples can use `[torch.FloatTensor, torch.LongTensor]`. |

## Return values

### `summary`

```python
total_params, trainable_params = summary(model, input_size, device="cpu")
```

`summary` calls `summary_string`, prints the returned summary string to standard
output, and returns the parameter-info tuple `(total_params, trainable_params)`.

### `summary_string`

```python
summary_text, (total_params, trainable_params) = summary_string(
    model,
    input_size,
    device="cpu",
)
```

`summary_string` returns:

1. `summary_text`: the formatted table string.
2. `(total_params, trainable_params)`: total and trainable parameter counts.

Under modern PyTorch, parameter counts may be Python integers or scalar tensor
objects. Normalize before strict comparisons or JSON serialization:

```python
def as_int(value):
    if hasattr(value, "item"):
        return int(value.item())
    return int(value)

assert as_int(total_params) == 21840
```

## `input_size` semantics

`input_size` excludes batch. The function creates synthetic tensors and runs one
forward pass through the model.

Single-input model:

```python
summary(model, input_size=(channels, height, width), device="cpu")
```

Multiple-input model:

```python
summary(model, input_size=[(1, 300), (1, 300)], device="cpu")
```

Important distinctions:

- A tuple means exactly one input tensor.
- A list of tuples means multiple input tensors passed as `model(*inputs)`.
- Do not include the batch dimension in any tuple.
- For a pure vector input, use the non-batch feature shape required by the
  model, for example `(300,)` or `(1, 300)` depending on what the model's
  `forward` expects.
- The generated tensors use internal batch size `2`; the `batch_size` argument
  only changes displayed shapes and memory estimates.

## Device semantics

The default `device` is `torch.device("cuda:0")`. This is easy to miss on
CPU-only hosts.

CPU-safe pattern:

```python
import torch
from torchsummary import summary

device = torch.device("cpu")
model = model.to(device)
summary(model, input_size=(1, 28, 28), device=device)
```

Optional CUDA pattern:

```python
import torch
from torchsummary import summary

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = model.to(device)
summary(model, input_size=(1, 28, 28), device=device)
```

The generated inputs and the model parameters must live on the same device.
`torchsummary` only moves its synthetic inputs; it does not call `model.to`.

## Dtype semantics

When `dtypes` is omitted, generated inputs are floating tensors. When present,
`dtypes` must be a list aligned with `input_size`:

```python
import torch
from torchsummary import summary

summary(
    model,
    input_size=[(1, 300), (1, 300)],
    device="cpu",
    dtypes=[torch.FloatTensor, torch.LongTensor],
)
```

Use this when a model's `forward(self, x_float, x_ids)` expects different input
kinds. The model itself must still make valid PyTorch operations with those
inputs. For example, a branch that sends a long tensor through `nn.Linear` must
convert it to floating point before the linear layer.

## Hook and row semantics

`torchsummary` registers forward hooks on modules except `nn.Sequential` and
`nn.ModuleList`. Consequences:

- Leaf layers such as `Conv2d`, `Linear`, `Dropout`, and `ReLU` appear as rows.
- `nn.Sequential` and `nn.ModuleList` containers are skipped as rows, while
  their child modules can still appear.
- Custom wrapper or root modules may appear as 0-parameter rows in newer PyTorch
  versions. Parameter totals still come from parameter-owning modules.
- The summary forward pass executes real model code with synthetic tensors, so
  invalid shapes, incompatible dtypes, missing keyword-only inputs, or unsupported
  output structures can still fail.

## Output table and memory estimates

The printed table includes layer names, output shapes, and parameter counts,
then totals and rough memory estimates:

- `Total params`: sum of parameters attached to hooked modules.
- `Trainable params`: parameters whose `weight.requires_grad` is true when the
  hook inspects the module.
- `Non-trainable params`: total minus trainable.
- `Input size (MB)`: approximate input tensor storage using 4 bytes per number.
- `Forward/backward pass size (MB)`: approximate output/gradient storage using
  a 2x multiplier.
- `Params size (MB)`: approximate parameter storage using 4 bytes per parameter.
- `Estimated Total Size (MB)`: sum of the above estimates.

Treat memory values as orientation-only. They do not replace a PyTorch profiler
or framework-specific memory accounting, and they assume simple tensor outputs
and 4-byte values.

## When to prefer `torchinfo`

Prefer `torchinfo` for advanced or new projects when you need:

- Better support for modern PyTorch features and maintained behavior.
- Complex nested, dictionary, or non-tensor inputs/outputs.
- Explicit sample input data rather than shape-only synthetic tensors.
- More configurable depth, column, and dtype reporting.
- More reliable behavior for wrapper modules, dynamic control flow, or models
  with unusual `forward` signatures.
- More credible memory reporting for planning or deployment decisions.

Use `torchsummary` when you need the small legacy API, quick parameter counts,
or compatibility with code that already calls `summary`/`summary_string`.
