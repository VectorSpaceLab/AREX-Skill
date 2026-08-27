# Repo Provenance

This generated skill was created from a Nilearn source checkout. Use this file
when deciding whether the skill is stale and should be refreshed.

## Source Snapshot

| Field | Value |
| --- | --- |
| Repository | Nilearn |
| Distribution/import name | `nilearn` |
| Source commit | `eb8854ce3ee75759a5c09655a1556894ae501b28` |
| Branch | `main` |
| Exact tag | none detected |
| Working tree state at generation | dirty: generated `skills/` tree was untracked |
| Package version observed during inspection | `0.1.dev1+geb8854ce3` |
| Remote URL | public: `https://github.com/nilearn/nilearn.git` |

The working tree dirtiness was caused by the generated skill and review
artifacts. No pre-existing source-file modifications were detected before skill
creation.

## Evidence Paths

Public runtime content was distilled from these repository-relative evidence
areas:

- `pyproject.toml`, `tox.ini`, `README.rst`, `AGENTS.md`
- `nilearn/`
- `nilearn/tests/` and module-specific `nilearn/*/tests/`
- `doc/modules/`, `doc/glm/`, `doc/decoding/`, `doc/connectivity/`,
  `doc/manipulating_images/`, `doc/plotting/`, `doc/building_blocks/`
- `examples/00_tutorials/` through `examples/07_advanced/`
- `maint_tools/` and `build_tools/` as maintainer evidence only

## Inspection Summary

The private inspection environment verified:

- Python package metadata for `nilearn`
- Imports for `nilearn`, `nilearn.image`, `nilearn.maskers`, `nilearn.glm`,
  `nilearn.decoding`, `nilearn.connectome`, and `nilearn.plotting`
- Core dependencies plus the `plotting` extra
- No package console scripts
- Safe no-network smoke helpers bundled in this skill

Private environment paths and local setup commands are intentionally omitted
from this public runtime skill.
