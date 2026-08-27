---
name: contribution-and-testing
description: "Use for TorchGeo repository edits, style/type conventions, adding
  datasets/models/tasks/transforms, fake fixtures, docs updates, and targeted
  verification commands."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# TorchGeo contribution and testing

Use this sub-skill when modifying the TorchGeo repository rather than only using the package.

## Required style conventions

- New Python files must start with:

```python
# Copyright (c) TorchGeo Contributors. All rights reserved.
# Licensed under the MIT License.
```

- Ruff style uses single quotes and isort ordering: stdlib, third-party, then local imports.
- All functions need type annotations. Prefer built-in collection types and `X | Y` unions.
- Use Google-style docstrings with `Args`, `Returns`, `Raises`, and `Warns` sections as needed.
- Avoid broad `Exception` catches. Use TorchGeo dataset errors such as `DatasetNotFoundError`, `RGBBandsMissingError`, or `DependencyNotFoundError` where applicable.

## New dataset checklist

1. Add `torchgeo/datasets/<dataset>.py` with the license header.
2. Import it in `torchgeo/datasets/__init__.py`.
3. Add generated/minimal fake data under `tests/data/<dataset>/`.
4. Add `tests/datasets/test_<dataset>.py` with enough coverage for initialization, `__getitem__`, plotting, missing data, checksum/download behavior, and split handling as applicable.
5. Update `docs/api/datasets.rst` and the relevant dataset CSV under `docs/api/datasets/`.
6. Add or update a datamodule and datamodule test if the dataset has a standard training workflow.

## Targeted commands

From the repository root:

```bash
ruff format && ruff check && ty check && prettier --write .
pytest --cov=torchgeo tests/
pytest --cov=torchgeo.datasets tests/datasets/test_<dataset>.py
pytest --cov=torchgeo.datasets tests/datasets/test_<dataset>.py::TestDataset::test_getitem
pytest -m "" --cov=torchgeo tests/  # includes slow tests, use only when approved
```

For docs, install docs dependencies and run:

```bash
cd docs && make clean && make html
```

## Testing practices

- Use fake data only; never commit real dataset samples.
- Mark downloads/network as `@pytest.mark.slow` and respect the default socket-disabled test settings.
- Use `pytest.importorskip` for optional dependencies.
- Close matplotlib figures in plot tests.
- Keep files reasonably small and separate logical changes.

## Read next

- [reference](references/contribution-and-testing.md) for review checklists and native test maps.
