# Repository Provenance

Generated skill id: `prolif`
Public project name: ProLIF
Package distribution name: `prolif`
Observed package version during inspection: `0.0.0`

## Source Snapshot

- VCS: git
- Branch: `master`
- Commit: `6d993eb1b54cd20cc160461dba1ee5e775cb4037`
- Exact tag: none detected
- Remote URL: `https://github.com/chemosim-lab/ProLIF.git`
- Working tree state at generation: dirty because the generated `skills/` directory and review artifacts were added during skill creation
- Source changes outside generated skill/artifact outputs: none detected from `git status --short` before generation

## Evidence Paths

- `pyproject.toml`
- `README.rst`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `CITATION.cff`
- `MANIFEST.in`
- `prolif/`
- `prolif/data/`
- `docs/source/`
- `docs/notebooks/`
- `tests/`
- `scripts/check_types.py`
- `scripts/test_build.py`

## Inspection Summary

The package was inspected from an isolated private Python environment with ProLIF installed in editable mode plus tutorial/plotting dependencies. Verified runtime facts included top-level imports, available interaction names, core API signatures, optional plotting imports, `pip check`, and a one-frame package-data fingerprint smoke run. Private environment paths and local executable details are intentionally omitted from this public provenance file.

## Refresh Signals

Refresh this skill when ProLIF changes any of these areas:

- `Fingerprint` constructor, execution, export, plotting, or parallel behavior
- interaction class names, parameters, defaults, implicit-hydrogen handling, or `WaterBridge`
- `Molecule`, suppliers, residue identifiers, standardization, or packaged data APIs
- plotting class signatures or optional dependency requirements
- package metadata dependencies, extras, supported Python versions, or public installation guidance
