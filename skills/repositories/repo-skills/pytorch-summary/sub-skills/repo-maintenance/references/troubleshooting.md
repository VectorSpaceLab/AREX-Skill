# repo-maintenance troubleshooting

Use this guide when maintaining the `torchsummary` source or diagnosing why native unit tests fail after a source, packaging, or documentation edit. For user-level `summary(...)` workflows and model-input troubleshooting, route to [`../../model-summary-usage/SKILL.md`](../../model-summary-usage/SKILL.md). For shared generated-bundle install/import notes, see [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md) when present.

## Missing runtime dependencies

Symptom examples:

```text
ModuleNotFoundError: No module named 'torch'
ModuleNotFoundError: No module named 'numpy'
```

Cause: package metadata has no `install_requires`, but runtime source imports both `torch` and `numpy`.

Fix in the active environment:

```bash
python -m pip install torch numpy
python -m pip check
python - <<'PY'
import numpy
import torch
import torchsummary
print("ok", torch.__version__, numpy.__version__, torchsummary.__file__)
PY
```

If the maintenance task is to improve packaging metadata, declare only true core dependencies (`torch`, `numpy`) or document them clearly. Do not add `torchvision` as a core dependency for this package just because a README example uses VGG16.

## Importing the wrong checkout

Symptom examples:

- A source edit has no effect.
- `inspect.signature(torchsummary.summary)` does not match the expected signature.
- Tests pass or fail differently from the edited files.

Check import identity:

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

If the module file does not belong to the checkout under maintenance, reinstall editable from the checkout root:

```bash
python -m pip install -e .
python -m unittest torchsummary.tests.unit_tests.torchsummary_test
```

## CPU-only failures from the default CUDA device

Symptom examples:

```text
AssertionError: Torch not compiled with CUDA enabled
RuntimeError: Found no NVIDIA driver on your system
RuntimeError: Expected all tensors to be on the same device
```

The public function default is `device=torch.device('cuda:0')`. On CPU-only hosts, tests and examples must pass `device="cpu"` explicitly:

```python
from torchsummary import summary
summary(model, input_size, device="cpu")
```

Do not silently change the default device in source as a maintenance shortcut; that changes the public signature and may invalidate generated documentation. If a device behavior change is intentional, update tests, docs, and generated skill references together.

Run the device-focused test:

```bash
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_single_layer_network_on_gpu
```

This test is safe on CPU-only machines because it falls back to CPU when CUDA is unavailable.

## Dtype ordering and device interactions

Symptom examples:

- Multiple-input model receives the wrong dtype per branch.
- A CUDA test fails after a model or fixture casts a tensor with legacy CPU tensor classes.
- A model forward reports missing positional arguments after a `dtypes` edit.

The implementation pairs `input_size` and `dtypes` in order. Preserve this order:

```python
dtypes = [torch.FloatTensor, torch.LongTensor]
summary(model, [input1, input2], device="cpu", dtypes=dtypes)
```

Run the dtype-focused test:

```bash
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_multiple_input_types
```

Maintenance caution: the bundled dtype fixture is CPU-oriented. If extending dtype behavior to CUDA, avoid forcing tensors back to CPU in model code; use device-aware casts such as `.float()` or `.to(dtype=...)` on existing tensors.

## `input_size` tuple/list regressions

Symptom examples:

- A single-input CNN suddenly calls the model with too many inputs.
- A multiple-input model receives one tuple instead of two tensors.
- Extra or missing generated synthetic inputs after validation changes.

Preserve the established semantics:

- `input_size=(1, 28, 28)` means one input tensor with shape `(2, 1, 28, 28)` during the synthetic forward.
- `input_size=[(1, 300), (1, 300)]` means two synthetic input tensors.
- `dtypes` must align with the list of input shapes. If adding validation, fail clearly on length mismatch rather than silently changing pairing behavior.

Run both focused tests:

```bash
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_single_input
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_multiple_input
```

## Parameter count type differences on modern PyTorch

Symptom examples:

- A direct comparison sees `tensor(21840)` instead of `21840`.
- Formatting or JSON serialization fails on scalar tensor counts.

The source accumulates parameter counts through PyTorch tensor operations. Existing native tests compare returned counts to Python integers and are the compatibility gate. For maintenance-only diagnostics, normalize with `int(total_params)` when printing, serializing, or writing synthetic checks. Do not change the public return type casually unless tests/docs are updated.

Quick diagnostic:

```bash
python - <<'PY'
import torch
from torchsummary import summary
model = torch.nn.Linear(2, 5)
total, trainable = summary(model, (1, 2), device="cpu")
print(type(total), total, int(total))
print(type(trainable), trainable, int(trainable))
PY
```

## Extra 0-parameter row for wrapper modules

Symptom examples:

- The printed table includes a custom root/wrapper module row with `0` params.
- A maintainer tries to remove rows by filtering hooks more aggressively.

The implementation registers forward hooks on modules that are not `nn.Sequential` and not `nn.ModuleList`. Custom wrapper modules may therefore appear with zero parameters. This does not necessarily mean counts are wrong. Before changing hook filtering, run:

```bash
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_single_input
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_multiple_input
```

If a formatting-only edit removes or renames rows, update string/table documentation and any tests that depend on the printed layout.

## `summary_string` return or table formatting changed

Symptom examples:

- `summary_string(...)` no longer returns a string as its first value.
- The printed table loses `Layer (type)`, `Output Shape`, or `Param #`.
- Totals are missing or renamed.

Preserve table and return contracts unless performing a deliberate public API change:

```bash
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummarystringTests.test_single_input
```

Manual smoke:

```bash
python - <<'PY'
import torch
from torchsummary import summary_string
result, counts = summary_string(torch.nn.Linear(2, 5), (1, 2), device="cpu")
assert isinstance(result, str)
assert "Layer (type)" in result
assert "Output Shape" in result
assert "Param #" in result
assert int(counts[0]) == 15 and int(counts[1]) == 15
print("ok")
PY
```

## Real forward-pass side effects

Symptom examples:

- A model fails because the generated random input is semantically invalid.
- BatchNorm/dropout behavior differs from expectations.
- A model forward has side effects during summary.

`torchsummary` intentionally performs a real forward pass over random synthetic inputs. This is required for collecting hook output shapes. Tests are safe because their fixtures are tiny and accept random tensors. When maintaining code, avoid replacing the real forward with static shape inference unless redesigning the API and verification plan.

For unusual models, set the model to the desired mode before calling the API in examples or tests:

```python
model.eval()
summary(model, input_size, device="cpu")
```

## Legacy package and `torchinfo` note

If users or maintainers ask for features outside the current tested surface, remember that the README recommends `torchinfo`. For maintenance edits, keep `torchsummary` behavior stable. For new feature requests, document migration to `torchinfo` rather than expanding this legacy package without a new test plan.
