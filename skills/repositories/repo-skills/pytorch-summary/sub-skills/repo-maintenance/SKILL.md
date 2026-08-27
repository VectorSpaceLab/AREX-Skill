---
name: repo-maintenance
description: "Maintain the torchsummary checkout safely, including package
  layout, public exports, dependency caveats, focused unittest commands, and
  safe edit boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# repo-maintenance

Use this sub-skill when the task is to maintain, edit, test, package, or refresh the tiny `torchsummary` source checkout. It preserves the repository facts needed to make safe changes without reopening external project pages or depending on original checkout paths.

For user-level model summary calls, `input_size` usage, multiple-input workflows, return values, or interpreting the printed table, route to [`../model-summary-usage/SKILL.md`](../model-summary-usage/SKILL.md) instead.

## Route map

- Source layout, package metadata, dependency declaration gaps, focused tests, and safe edit boundaries: read [`references/testing-and-maintenance.md`](references/testing-and-maintenance.md).
- Maintenance failures, import confusion, CPU/CUDA device issues, dtype pitfalls, and modern PyTorch count comparisons: read [`references/troubleshooting.md`](references/troubleshooting.md).
- Cross-skill install/import provenance and shared package troubleshooting: see the root skill references [`../../references/repo-provenance.md`](../../references/repo-provenance.md) and [`../../references/troubleshooting.md`](../../references/troubleshooting.md) when those root files are present in the generated bundle.

## Essential facts

- Distribution/import module: `torchsummary`.
- Source package version: `1.5.1` from `setup.py`.
- Public exports from `torchsummary/__init__.py`: `summary` and `summary_string`.
- Installed/source signatures verified for both public functions:
  - `summary(model, input_size, batch_size=-1, device=torch.device("cuda:0"), dtypes=None)`
  - `summary_string(model, input_size, batch_size=-1, device=torch.device("cuda:0"), dtypes=None)`
- `setup.py` declares `packages=["torchsummary"]` and no `install_requires`, but runtime source imports both `torch` and `numpy`.
- The implementation creates random synthetic inputs and runs a real forward pass through the supplied `torch.nn.Module`; tests are small and safe, but require working `torch` and `numpy` imports.
- The README begins with a deprecation/migration note recommending the newer `torchinfo` project. Preserve that note when editing docs, and prefer migration advice rather than adding broad new features to this legacy package.

## Quick maintainer loop

From the repository root of the checkout being edited:

```bash
python - <<'PY'
import inspect
import torchsummary
print(torchsummary.__file__)
print(inspect.signature(torchsummary.summary))
print(inspect.signature(torchsummary.summary_string))
PY

python -m unittest torchsummary.tests.unit_tests.torchsummary_test
```

If the full unit module fails, run the focused test IDs in [`references/testing-and-maintenance.md`](references/testing-and-maintenance.md), fix the smallest behavior boundary that explains the failure, then rerun the focused test and the full unit module.

## Do not change casually

Treat the following as compatibility boundaries unless tests, docs, and generated skill references are updated together:

- Public function names, exports, signatures, defaults, return values, and print behavior.
- `input_size` semantics: tuple means one input; list of tuples means multiple inputs.
- Tuple/list handling for model outputs in the summary table.
- Per-input `dtypes` order and length expectations.
- Device behavior, especially the default `cuda:0` signature and explicit `device="cpu"` usage on CPU-only hosts.
- Printed table columns and totals: `Layer (type)`, `Output Shape`, `Param #`, total/trainable/non-trainable params, and size estimates.
