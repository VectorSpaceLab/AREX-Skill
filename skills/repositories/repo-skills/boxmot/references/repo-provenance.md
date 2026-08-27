# Repo Provenance

schema: `disco.repo-provenance.v1`

## Source snapshot

- Repository: `mikel-brostrom/boxmot`
- Public remote: `https://github.com/mikel-brostrom/boxmot.git`
- Branch: `master`
- Commit: `b23bf5f453d57c3fa3243e6648af6ea6738575b4`
- Source package metadata version: `22.0.0` from `pyproject.toml`
- Runtime import version observed during inspection: `19.0.0` from `boxmot.__version__`
- Dirty state at skill generation: untracked generated skill/review artifacts were present under `skills/`; source files used as evidence were not modified for this skill.

## Version caveat

`pyproject.toml` reports `22.0.0`, while `boxmot.__version__` reports `19.0.0` in the inspected package. Treat this as a staleness/troubleshooting caveat: when behavior differs from this skill, re-check both package metadata and live import version before assuming the repo or installed package is stale.

## Evidence paths consulted

- `README.md`
- `pyproject.toml`
- `boxmot/__init__.py`
- `boxmot/engine/cli.py`
- `boxmot/pipeline.py`
- `boxmot/api/`
- `boxmot/configs/`
- `boxmot/configs/modes.yaml`
- `boxmot/configs/benchmarks/*.yaml`
- `boxmot/configs/trackers/*.yaml`
- `boxmot/trackers/`
- `boxmot/trackers/base.py`
- `boxmot/trackers/registry.py`
- `boxmot/trackers/results.py`
- `boxmot/trackers/common/detections/layout.py`
- `boxmot/trackers/common/geometry/obb.py`
- `boxmot/reid/`
- `boxmot/engine/reid/`
- `boxmot/native/`
- `boxmot/native/registry.py`
- `boxmot/native/cpp/README.md`
- `docs/getting-started/installation.md`
- `docs/modes/`
- `docs/guides/`
- `docs/concepts/`
- `docs/python/`
- `docs/native/index.md`
- `docs/trackers/`
- `tests/unit/test_cli.py`
- `tests/unit/test_python_api.py`
- `tests/unit/test_trackers.py`
- `tests/unit/test_bbox_tracker_contract.py`
- `tests/unit/test_common_obb.py`
- `tests/unit/test_base_backend.py`
- `tests/unit/test_dataset_config.py`
- `tests/unit/test_native_bytetrack.py`
- `tests/unit/test_native_botsort.py`
- `tests/unit/test_native_ocsort.py`
- `tests/unit/test_native_sfsort.py`

## Refresh guidance

Refresh this skill if the public CLI modes, tracker registry, OBB layouts, benchmark config schema, ReID training/export options, native backend registry, or package version facts change.
