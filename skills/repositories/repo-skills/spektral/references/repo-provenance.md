# Spektral Repository Provenance

- Schema: `disco.repo-provenance.v1`

## Source snapshot

- VCS: git
- Repository: Spektral
- Remote URL: https://github.com/danielegrattarola/spektral.git
- Branch: `master`
- Commit: `a5fa5e38fca4eaca1e47ccfe1b00e0a61f64648b`
- Exact tag: none detected at this commit
- Package version: `1.3.1` from `pyproject.toml` and `spektral.__version__`
- Working tree state during construction: dirty; untracked relative path `skills/` was present for generated skill and review artifacts.

## Evidence paths used

The skill was distilled from these source-relative paths:

- `pyproject.toml`
- `setup.py`
- `README.md`
- `CONTRIBUTING.md`
- `spektral/__init__.py`
- `spektral/data/`
- `spektral/datasets/`
- `spektral/layers/`
- `spektral/models/`
- `spektral/transforms/`
- `spektral/utils/`
- `docs/mkdocs.yml`
- `docs/templates/`
- `examples/`
- `tests/`

## Refresh guidance

Refresh this skill if the package version, source commit, public API signatures, loader semantics, layer mode support, dataset catalog, or TensorFlow/Keras compatibility changes. Treat changes under `spektral/data/`, `spektral/layers/`, `spektral/models/`, `spektral/transforms/`, `spektral/utils/`, `docs/templates/`, `examples/`, or `tests/` as relevant for staleness checks.
