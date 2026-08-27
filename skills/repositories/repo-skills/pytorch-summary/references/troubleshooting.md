# pytorch-summary Troubleshooting

Use this root troubleshooting guide for cross-cutting install, import, backend,
and package-selection failures. For model-input details, route to
[`../sub-skills/model-summary-usage/SKILL.md`](../sub-skills/model-summary-usage/SKILL.md).
For source-maintenance failures, route to
[`../sub-skills/repo-maintenance/SKILL.md`](../sub-skills/repo-maintenance/SKILL.md).

## Missing `torch` or `numpy`

Symptoms:

```text
ModuleNotFoundError: No module named 'torch'
ModuleNotFoundError: No module named 'numpy'
```

Cause: `torchsummary` `1.5.1` imports both packages, but the legacy packaging
metadata does not declare them as install requirements.

Fix:

```bash
python -m pip install numpy
# Install the PyTorch build that matches your platform/backend from the official PyTorch instructions.
python -m pip install torchsummary
python scripts/check_install.py --device cpu
```

Do not add `torchvision` unless a task specifically uses a `torchvision` model;
`torchvision` appears only in a large README example and is not a core package
requirement.

## CPU-only host fails before summary starts

Symptoms often mention CUDA initialization, a missing NVIDIA driver, or a torch
build without CUDA. The public default is `device=torch.device("cuda:0")`.

Use CPU explicitly:

```python
import torch
from torchsummary import summary

device = torch.device("cpu")
model = model.to(device)
summary(model, input_size=(1, 28, 28), device=device)
```

If CUDA is desired, first verify that the target runtime actually has a CUDA
PyTorch build and a visible GPU:

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
PY
```

## Model and generated inputs are on different devices

Symptoms:

```text
RuntimeError: Expected all tensors to be on the same device
```

`torchsummary` moves only its synthetic inputs to the `device` argument; it does
not move the model. Use one device object consistently:

```python
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = model.to(device)
summary(model, input_size=(channels, height, width), device=device)
```

## Importing a different `torchsummary` than intended

Symptoms:

- Source edits do not affect behavior.
- Signatures differ from the expected legacy signatures.
- Tests pass or fail differently across shells.

Check identity and signatures:

```bash
python - <<'PY'
import inspect
import torchsummary
print(torchsummary.__file__)
print(inspect.signature(torchsummary.summary))
print(inspect.signature(torchsummary.summary_string))
PY
```

Expected signatures:

```text
summary(model, input_size, batch_size=-1, device=torch.device("cuda:0"), dtypes=None)
summary_string(model, input_size, batch_size=-1, device=torch.device("cuda:0"), dtypes=None)
```

For a local editable checkout, reinstall from that checkout root:

```bash
python -m pip install -e .
python -m pip check
```

## Smoke helper separates package failures from model failures

Run the root diagnostic first:

```bash
python scripts/check_install.py --device cpu
```

Then run the model-summary workflow smoke helper:

```bash
python sub-skills/model-summary-usage/scripts/smoke_summary.py --case all --device cpu
```

If both pass, a remaining failure is probably in the user's model shape, dtype,
output structure, or device placement. Continue in
[`../sub-skills/model-summary-usage/references/troubleshooting.md`](../sub-skills/model-summary-usage/references/troubleshooting.md).

## Legacy package selection

The source README starts by recommending `torchinfo`. Prefer `torchinfo` rather
than extending `torchsummary` when a task needs modern PyTorch features,
non-positional inputs, complex nested outputs, configurable display depth, or
more trustworthy memory accounting.
