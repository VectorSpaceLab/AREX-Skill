# Testing and maintenance guide

This guide is for future agents editing or refreshing the `torchsummary` package source. It is self-contained: use the repository-relative paths and commands below from the checkout you are maintaining.

For end-user model-summary workflows, route to [`../../model-summary-usage/SKILL.md`](../../model-summary-usage/SKILL.md). For shared generated-bundle provenance, see [`../../../references/repo-provenance.md`](../../../references/repo-provenance.md) when the root bundle is present.

## Source layout to preserve

The source snapshot used for this skill has these Git-tracked files:

| Path | Maintenance role |
| --- | --- |
| `.gitignore` | Ignore/cache policy for local development artifacts. |
| `LICENSE` | MIT license text. |
| `README.md` | User-facing install/usage examples and the leading migration note recommending `torchinfo`. |
| `setup.py` | Packaging metadata for distribution `torchsummary` version `1.5.1`. |
| `torchsummary/__init__.py` | Public re-export surface: `summary`, `summary_string`. |
| `torchsummary/torchsummary.py` | Entire runtime implementation: input construction, forward hooks, table formatting, count/size calculation. |
| `torchsummary/tests/test_models/test_model.py` | Tiny test model fixtures used by unit tests. |
| `torchsummary/tests/unit_tests/torchsummary_test.py` | Ground-truth unit tests for single-input, multiple-input, dtype, device, and `summary_string` behavior. |

There are no source-owned standalone scripts, CLI tools, or benchmark programs in the tracked snapshot. README examples and unit-test fixtures are the relevant behavioral evidence.

## Package metadata and dependency caveat

`setup.py` defines:

```python
setup(
    name="torchsummary",
    version="1.5.1",
    description="Model summary in PyTorch similar to `model.summary()` in Keras",
    url="https://github.com/sksq96/pytorch-summary",
    packages=["torchsummary"],
)
```

Important caveat: `setup.py` has no `install_requires`, but `torchsummary/torchsummary.py` imports `torch` and `numpy`. Maintainers must therefore ensure the active test/runtime environment already has both packages installed. If packaging metadata is updated, add only the true core runtime dependencies; do not claim `torchvision` is required for the core package because it appears only in a large README example.

The package is legacy: the README begins by recommending the newer `torchinfo` project. Preserve that deprecation/migration note in documentation edits, and consider recommending `torchinfo` for new feature requests rather than expanding this package beyond its tested compatibility surface.

## Public API surface

`torchsummary/__init__.py` exports exactly:

```python
from .torchsummary import summary, summary_string
```

The verified public signatures are:

```text
summary(model, input_size, batch_size=-1, device=torch.device("cuda:0"), dtypes=None)
summary_string(model, input_size, batch_size=-1, device=torch.device("cuda:0"), dtypes=None)
```

Public behavior to preserve:

- `summary(...)` calls `summary_string(...)`, prints the formatted string, and returns `(total_params, trainable_params)`.
- `summary_string(...)` returns `(summary_str, (total_params, trainable_params))`.
- `input_size=(C, H, W)` means one model input. `input_size=[shape1, shape2, ...]` means multiple model inputs.
- `dtypes` is a per-input list paired with `input_size` in order. The dtype order matters.
- The default device in the signature is CUDA-like (`cuda:0`); CPU-only validation must pass `device="cpu"` explicitly.
- The implementation generates random synthetic inputs with a real batch dimension of `2` for the forward pass, then displays the user-facing `batch_size` value in recorded shapes.
- The implementation performs an actual `model(*inputs)` forward pass and registers forward hooks on non-`Sequential`/non-`ModuleList` modules.

## Maintainer environment checks

Run these commands from the checkout root before editing or when tests import the wrong package:

```bash
python - <<'PY'
import inspect
import numpy
import torch
import torchsummary
print("torchsummary file:", torchsummary.__file__)
print("torch:", torch.__version__)
print("numpy:", numpy.__version__)
print("summary:", inspect.signature(torchsummary.summary))
print("summary_string:", inspect.signature(torchsummary.summary_string))
PY
```

The printed `torchsummary file` should point to the checkout you intend to edit, or to an editable install of it. If it points elsewhere, reinstall the package from the checkout:

```bash
python -m pip install -e .
python -m pip check
```

Because dependencies are undeclared, install or repair `torch` and `numpy` explicitly in the active environment if imports fail.

## Full and focused tests

Run the full native unit module:

```bash
python -m unittest torchsummary.tests.unit_tests.torchsummary_test
```

Use focused test IDs when narrowing a failure:

```bash
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_single_input
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_multiple_input
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_single_layer_network
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_single_layer_network_on_gpu
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_multiple_input_types
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummarystringTests.test_single_input
```

### What the focused tests assert

| Test ID suffix | Behavior covered | Expected signal |
| --- | --- | --- |
| `torchsummaryTests.test_single_input` | CNN-style single input `(1, 28, 28)` on CPU. | `summary(...)` returns total/trainable params `21840`. |
| `torchsummaryTests.test_multiple_input` | Model with two inputs, passed as `[input1, input2]`, on CPU. | Total/trainable params `31120`. |
| `torchsummaryTests.test_single_layer_network` | Single `torch.nn.Linear(2, 5)` on CPU. | Total/trainable params `15`. |
| `torchsummaryTests.test_single_layer_network_on_gpu` | Device branch that uses CUDA when available and CPU otherwise. | Total/trainable params `15`; CUDA is optional because the test falls back to CPU. |
| `torchsummaryTests.test_multiple_input_types` | Per-input `dtypes=[torch.FloatTensor, torch.LongTensor]` order on CPU. | Total/trainable params `31120`. |
| `torchsummarystringTests.test_single_input` | Programmatic return contract for `summary_string`. | First return value is `str`; counts are `21840`, `21840`. |

These tests are safe and small, but they require `torch` and `numpy` because the implementation creates random tensors and performs real forwards.

## Safe edit guidance

Before changing runtime code, identify which compatibility boundary is involved:

1. Reproduce the failing focused test or a minimal smoke command.
2. Confirm imports and public signatures with the environment check above.
3. Patch the smallest source region that explains the failure.
4. Rerun the focused test that failed.
5. Rerun the full unit module.
6. If metadata changed, rerun `python -m pip install -e .` and `python -m pip check`.
7. If public behavior changed intentionally, update generated skill references and relevant tests/docs together.

Do not change these casually:

- Public function signatures, default values, exported names, return tuple shapes, and `summary(...)` print behavior.
- `input_size` conversion: tuple as single input; list of tuples as multiple inputs.
- Forward-hook filtering and tuple/list output handling; parameter totals rely on collecting module hooks without double-counting trainable weights.
- `dtypes` pairing with inputs. Preserve order and make length mismatches explicit if adding validation.
- `device` behavior. CPU users should pass `device="cpu"`; changing the default away from `cuda:0` is a public-signature change.
- The summary table columns and totals: `Layer (type)`, `Output Shape`, `Param #`, `Total params`, `Trainable params`, `Non-trainable params`, and size estimates.
- Synthetic-input semantics: the helper creates inputs internally and performs a real model forward. Do not remove the forward pass unless the API is redesigned and tests/docs are updated.

## Common maintenance scenarios

### Updating dependency metadata

Acceptable core metadata fix:

- Document or declare `torch` and `numpy` as runtime dependencies.
- Keep `torchvision` out of core requirements unless adding an optional extra specifically for README-style large-model examples.
- Reinstall editable and run `python -m pip check` plus the full unit module.

### Editing hook collection or table formatting

Run at least:

```bash
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_single_input
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_multiple_input
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummarystringTests.test_single_input
```

These catch parameter totals, multiple-input paths, and string-return regressions. Also manually inspect the printed output if columns or formatting changed.

### Editing dtype or device handling

Run at least:

```bash
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_multiple_input_types
python -m unittest torchsummary.tests.unit_tests.torchsummary_test.torchsummaryTests.test_single_layer_network_on_gpu
```

The dtype case is CPU-oriented. If adding CUDA dtype coverage, ensure model code does not force tensors back to CPU with legacy tensor classes.
