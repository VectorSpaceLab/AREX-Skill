# torchsummary Usage Workflows

Use these recipes to call `torchsummary.summary` and
`torchsummary.summary_string` correctly in ordinary PyTorch projects.

## Quick import check

Run this in the target Python runtime before diagnosing model-specific failures:

```bash
python - <<'PY'
import inspect
import numpy
import torch
from torchsummary import summary, summary_string

print("torch", torch.__version__)
print("numpy", numpy.__version__)
print("summary", inspect.signature(summary))
print("summary_string", inspect.signature(summary_string))
PY
```

If this fails for missing `torch` or `numpy`, install them explicitly. The
`torchsummary` package metadata for version `1.5.1` does not declare those
runtime dependencies even though the implementation imports them.

## Workflow 1: single-input model

Use a tuple for one input. The tuple excludes batch.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchsummary import summary, summary_string

class SmallCnn(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2(x), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        return self.fc2(x)

device = torch.device("cpu")
model = SmallCnn().to(device)
model.eval()

# Prints the table and returns (total_params, trainable_params).
total_params, trainable_params = summary(
    model,
    input_size=(1, 28, 28),
    device=device,
)

# Returns the table string instead of printing it.
summary_text, (total_params, trainable_params) = summary_string(
    model,
    input_size=(1, 28, 28),
    device=device,
)
```

Parameter counts may be Python integers or scalar tensors. For assertions:

```python
def as_int(value):
    return int(value.item()) if hasattr(value, "item") else int(value)

assert as_int(total_params) == as_int(trainable_params)
```

## Workflow 2: multiple-input model

Use a list of input-size tuples. Each tuple excludes batch. The generated
synthetic tensors are passed positionally as `model(*inputs)`.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchsummary import summary

class TwoBranchNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1a = nn.Linear(300, 50)
        self.fc1b = nn.Linear(50, 10)
        self.fc2a = nn.Linear(300, 50)
        self.fc2b = nn.Linear(50, 10)

    def forward(self, x1, x2):
        x1 = self.fc1b(F.relu(self.fc1a(x1)))
        x2 = self.fc2b(F.relu(self.fc2a(x2)))
        return torch.cat((x1, x2), dim=0)

device = torch.device("cpu")
model = TwoBranchNet().to(device)

summary(
    model,
    input_size=[(1, 300), (1, 300)],
    device=device,
)
```

Common mistakes:

- Do not use `input_size=((1, 300), (1, 300))`; a tuple is treated as one input.
- Keep the list order identical to the model's `forward` argument order.
- If the model expects keyword-only inputs or optional non-tensor metadata,
  this shape-only API may not be sufficient; prefer `torchinfo` or a custom
  probe.

## Workflow 3: per-input dtypes

Use `dtypes` when each generated input needs a different tensor type. The list
must align with the `input_size` list.

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

Model-side guidance:

- A long input can represent token IDs or index-like data.
- `nn.Linear` and most floating-point layers require floating-point tensors, so
  convert integer branches before those operations.
- For device-safe conversion, prefer `x.to(device=other.device,
  dtype=torch.float32)` over `x.type(torch.FloatTensor)`, because `.type` with a
  CPU tensor class can accidentally move data back to CPU.

## Workflow 4: CPU-first device handling

The public default device is CUDA (`cuda:0`). Use this pattern when portability
matters:

```python
import torch
from torchsummary import summary

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = model.to(device)
summary(model, input_size=(1, 28, 28), device=device)
```

For CPU-only troubleshooting, force both model and generated inputs to CPU:

```python
device = torch.device("cpu")
model = model.to(device)
summary(model, input_size=(1, 28, 28), device=device)
```

If the model already has buffers, embeddings, or submodules on a specific
device, move the whole module consistently before calling `summary`.

## Workflow 5: batch-size display semantics

`torchsummary` always creates synthetic inputs with internal batch size `2`.
The `batch_size` argument only changes the displayed first dimension and rough
memory estimate.

```python
summary(model, input_size=(1, 28, 28), batch_size=32, device="cpu")
```

This can print shapes such as `[32, 10]`, but it does not prove that the model
was executed with a real batch of 32. Do not use `batch_size` to test behavior
that depends on the actual runtime batch size.

## Workflow 6: interpret the summary output

Read the table as a lightweight diagnostic:

- Layer rows identify hooked modules and their output shapes.
- `Param #` is the parameter count attached to that module's `weight` and
  `bias` attributes.
- Reused modules can appear more than once because hooks fire on each forward
  use; interpret rows as forward calls, not necessarily unique module objects.
- Custom wrapper/root modules can appear as 0-parameter rows in newer PyTorch.
  Parameter totals remain useful if the parameter-owning modules are counted.
- `Total params` and `Trainable params` are the values returned by the API.
- Memory estimates are rough 4-byte-per-number calculations, not profiler-grade
  memory measurements.

## Workflow 7: run the bundled smoke helper

From this sub-skill directory:

```bash
python scripts/smoke_summary.py --help
python scripts/smoke_summary.py --case single --device cpu
python scripts/smoke_summary.py --case multi --device cpu
python scripts/smoke_summary.py --case dtype --device cpu
python scripts/smoke_summary.py --case all --device cpu
```

The documented parser options are exactly:

- `--case {single,multi,dtype,all}`: choose one deterministic smoke case or all
  cases.
- `--device DEVICE`: choose the device used for both the model and generated
  synthetic inputs. Use `cpu` for portable checks; use `cuda:0` only when a CUDA
  PyTorch runtime and GPU are available.
- `--help`: show argparse help.

The helper defines its own tiny models, imports only public `torchsummary` APIs,
uses no downloads, and asserts expected total/trainable parameter counts.

## Optional large-model note

A VGG-style `torchvision` example is a common demonstration, but it is optional,
requires `torchvision`, and can be memory-heavy. Do not use it as the minimum
smoke test. Start with the bundled tiny cases above; use `torchinfo` for newer
large-model inspection workflows when possible.

## Related references

- [API reference](api-reference.md)
- [Troubleshooting](troubleshooting.md)
- [Smoke helper](../scripts/smoke_summary.py)
