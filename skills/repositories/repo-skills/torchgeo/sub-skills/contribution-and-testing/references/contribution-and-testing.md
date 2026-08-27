# Contribution and testing reference

## Evidence map for common edits

- Dataset base behavior: `torchgeo/datasets/geo.py`, `torchgeo/datasets/utils.py`, `torchgeo/datasets/errors.py`.
- Dataset catalog docs: `docs/api/datasets.rst`, `docs/api/datasets/*.csv`, per-dataset RST files.
- Datamodule behavior: `torchgeo/datamodules/geo.py`, `torchgeo/datamodules/utils.py`, `tests/datamodules/`.
- Samplers: `torchgeo/samplers/`, `tests/samplers/`.
- Models and weights: `torchgeo/models/api.py`, family-specific `torchgeo/models/*.py`, `tests/models/`.
- Tasks: `torchgeo/tasks/*.py`, `tests/tasks/`.
- Transforms: `torchgeo/transforms/*.py`, `tests/transforms/`.
- Project metadata and dependencies: `pyproject.toml`, `uv.lock`.

## Review checklist for code changes

1. Public API imports are updated in `__init__.py` files.
2. Tests cover success and failure paths without network unless marked slow.
3. Fake data matches the real expected file structure and uses generated tiny fixtures.
4. Docs/catalog tables are updated for user-visible datasets/models/tasks.
5. Optional dependencies are lazy and have helpful error messages.
6. Tensor shapes and sample keys are documented or asserted in tests.
7. CRS/resolution/time behavior is explicit for geospatial data.
8. Band order and `in_channels` are consistent across datasets, transforms, and models.
9. New files include the license header.
10. Targeted pytest passes before broad test suites.

## Native candidate map

- CPU required: style/type checks, most dataset fake-fixture tests, sampler tests, transform tensor tests, model API construction tests, and task smoke tests with tiny data.
- Optional network/slow: dataset downloads, checksum tests against remote files, pretrained checkpoint downloads, docs notebooks that fetch data.
- Optional accelerator: training performance and large model workflows; CPU smoke is usually acceptable for API correctness.

## Dependency notes

TorchGeo currently targets Python `>=3.12`. The core dependency list is intentionally broad because TorchGeo spans geospatial IO, PyTorch training, model registries, and data augmentation. When adding a dependency, document why its minimum version is needed and update all relevant requirements/lock metadata.
