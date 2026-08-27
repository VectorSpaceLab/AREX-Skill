# Repo Provenance

schema: disco.repo-provenance.v1

## Source Snapshot

- Repository: Chemprop
- Package version from metadata and installed inspection: `2.2.3`
- Git commit: `bfdd2d4e91a77ef4d3e005324a2ecc166b358898`
- Git branch: `main`
- Exact tag: none recorded
- Working tree state at generation: dirty because DisCo-generated `skills/` content was present or being created
- Remote URL: https://github.com/chemprop/chemprop

## Evidence Paths

Runtime skill content was distilled from these repository-relative evidence paths:

- `pyproject.toml`
- `README.md`
- `chemprop/`
- `chemprop/cli/`
- `chemprop/data/`
- `chemprop/featurizers/`
- `chemprop/models/`
- `chemprop/nn/`
- `chemprop/uncertainty/`
- `docs/source/cmd.rst`
- `docs/source/quickstart.rst`
- `docs/source/installation.rst`
- `docs/source/tutorial/cli/`
- `docs/source/tutorial/python/`
- `examples/*.ipynb`
- `tests/cli/`
- `tests/integration/`
- `tests/unit/`
- `tests/data/` fixture shapes and example artifact names
- `requirements/`
- Existing repo-local guidance under `skills/chemprop/` as non-authoritative prior evidence

## Excluded Evidence

- `.git/`, caches, `__pycache__/`, generated build outputs, and generated docs outputs.
- `docs/source/_static/` image assets except as repository branding evidence.
- `skills/tests/` review artifacts.
- Maintainer fixture-regeneration scripts such as `tests/regenerate_models.sh` and `tests/data/mol_atom_bond/regenerate_models.sh`.
- Broad optional dev/docs/notebook extras not needed for base package inspection.

## Refresh Guidance

Refresh this skill if Chemprop changes CLI subcommands or flags, supported task/loss/metric registries, data schemas, model save/load behavior, optional extras, or Python public API signatures. Compare a future checkout against this commit and package version before assuming the generated skill is current.
