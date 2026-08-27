# TorchGeo repo provenance

- Repository: `torchgeo/torchgeo`
- Source commit: `51a30d67f28794090f88a59b91deeadf91de1878`
- Branch at distillation time: `main`
- Package name: `torchgeo`
- Package version in `pyproject.toml`: `0.11.0.dev1`
- License: MIT
- Python requirement: `>=3.12`
- Distillation mode: Creator fallback after repeated CLI resume attempts finished without a generated `SKILL.md`; no import was performed.

## Evidence paths used

- `README.md`
- `pyproject.toml`
- `AGENTS.md`
- `torchgeo/datasets/geo.py`
- `torchgeo/datasets/utils.py`
- `torchgeo/datasets/errors.py`
- `torchgeo/datamodules/geo.py`
- `torchgeo/datamodules/utils.py`
- `torchgeo/samplers/base.py`
- `torchgeo/samplers/single.py`
- `torchgeo/samplers/batch.py`
- `torchgeo/samplers/spatial.py`
- `torchgeo/samplers/temporal.py`
- `torchgeo/models/api.py`
- `torchgeo/models/*.py`
- `torchgeo/tasks/*.py`
- `torchgeo/transforms/*.py`
- `tests/datasets/test_*.py`
- `tests/datamodules/test_*.py`
- `tests/models/test_*.py`
- `tests/samplers/test_*.py`
- `tests/tasks/test_*.py`
- `tests/transforms/test_*.py`
- `docs/api/*.rst`
- `docs/api/datasets/*.csv`
- `docs/tutorials/`

## Staleness checks for future users

Before relying on this skill for code changes, compare the current checkout with the commit above. Re-open the relevant source module and test file when any of these change:

- Dataset base classes or utilities in `torchgeo/datasets/geo.py` or `torchgeo/datasets/utils.py`.
- Sampler constructor signatures or ROI/TOI behavior in `torchgeo/samplers/`.
- `BaseDataModule`, `GeoDataModule`, or `NonGeoDataModule` setup/dataloader behavior in `torchgeo/datamodules/geo.py`.
- Task constructor parameters, loss names, metric behavior, or plotting logic in `torchgeo/tasks/`.
- Model registry and weight enum wiring in `torchgeo/models/api.py`.
- Minimum dependency versions in `pyproject.toml`.
