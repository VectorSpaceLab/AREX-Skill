---
name: pytorch-summary
description: "Use and maintain the legacy torchsummary PyTorch model-summary
  package, including summary calls, device and dtype handling, smoke checks, and
  focused repo tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# pytorch-summary

Use this repo skill when a task names `pytorch-summary` or `torchsummary`, or
when a PyTorch model needs the legacy Keras-style `summary(...)` table for
output shapes, parameter counts, and rough size estimates.

This package is small and legacy. The source README recommends the newer
`torchinfo` project for new and more advanced model-inspection work. Use this
skill when existing code depends on `torchsummary`, when a task asks about this
repo/package specifically, or when the lightweight legacy API is enough.

## Quick install and import check

`torchsummary` version `1.5.1` imports both PyTorch and NumPy, but its packaging
metadata does not declare them as install requirements. Install PyTorch for the
intended backend first, then install `torchsummary` and `numpy` if needed.

CPU-oriented example:

```bash
python -m pip install numpy torchsummary
# install a PyTorch build appropriate for the target platform/backend separately
python - <<'PY'
from torchsummary import summary, summary_string
print(summary, summary_string)
PY
```

Run the bundled diagnostic when imports or device behavior are uncertain:

```bash
python scripts/check_install.py --help
python scripts/check_install.py --device cpu
```

The diagnostic is safe: it imports `torchsummary`, `torch`, and `numpy`, prints
public signatures, reports CUDA visibility, and runs a tiny `torch.nn.Linear`
summary on the requested device.

## Route map

- For end-user model inspection with `summary(...)` or `summary_string(...)`,
  read [`sub-skills/model-summary-usage/SKILL.md`](sub-skills/model-summary-usage/SKILL.md).
  This covers single inputs, multiple inputs, `dtypes`, CPU/CUDA placement,
  returned counts, table interpretation, and a bundled smoke helper.
- For editing this checkout, fixing tests, changing packaging metadata, or
  preserving source compatibility, read
  [`sub-skills/repo-maintenance/SKILL.md`](sub-skills/repo-maintenance/SKILL.md).
- For install/import, backend, dependency, and package-selection failures shared
  by both routes, read [`references/troubleshooting.md`](references/troubleshooting.md).
- Before deciding whether this generated skill is stale for a checkout, read
  [`references/repo-provenance.md`](references/repo-provenance.md).

## Public API facts

The package exports exactly the legacy public functions below:

```python
from torchsummary import summary, summary_string
```

Verified signatures:

```python
summary(model, input_size, batch_size=-1, device=torch.device("cuda:0"), dtypes=None)
summary_string(model, input_size, batch_size=-1, device=torch.device("cuda:0"), dtypes=None)
```

Key usage constraints:

- `model` must be a PyTorch `torch.nn.Module` and must already be on the same
  device passed as `device`.
- `input_size` excludes batch. Use a tuple for one input and a list of tuples
  for multiple positional inputs.
- The default device is CUDA; CPU-only use should pass `device="cpu"` or
  `torch.device("cpu")` explicitly.
- `dtypes`, when provided, is a list aligned with the `input_size` list.
- `summary(...)` prints a table and returns `(total_params, trainable_params)`.
- `summary_string(...)` returns `(summary_text, (total_params,
  trainable_params))`.

## Use `torchinfo` instead when

- The task is not tied to legacy `torchsummary` compatibility.
- The model needs dictionary, keyword-only, or non-tensor inputs.
- You need richer nested-module display, configurable columns/depth, or modern
  PyTorch behavior.
- Memory estimates must be credible enough for deployment planning.

## Verification baseline

This generated skill was built against `torchsummary` `1.5.1` with CPU PyTorch
verification. CUDA is documented as an optional device path, not a required
backend for this skill. Use `refresh-repo-skill` if the package source,
packaging metadata, public signatures, tests, or README guidance change.
