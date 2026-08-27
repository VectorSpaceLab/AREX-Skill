# Repo provenance

Schema: `disco.repo-provenance.v1`

## Source snapshot

- Repository: dottxt-ai/outlines
- Public remote URL: https://github.com/dottxt-ai/outlines.git
- Commit: `7d068478851f7ba76cb53997673d57f77b2d6f84`
- Branch: `main`
- Exact tag: none detected at generation time
- Package distribution: `outlines`
- Installed inspection version: `0.1.dev1+g7d0684788`
- Python support from metadata: `>=3.10,<3.14`

## Working tree state

The checkout was dirty during skill generation because `skills/` contained production logs, review artifacts, and generated skill output. No source-package paths under `src/outlines/`, docs, examples, tests, or package metadata were intentionally modified for this skill.

## Evidence paths

Primary evidence was taken from these repository-relative paths:

- `pyproject.toml`, `setup.cfg`, `environment.yml`, `uv.lock`
- `README.md`
- `src/outlines/__init__.py`
- `src/outlines/generator.py`
- `src/outlines/applications.py`
- `src/outlines/templates.py`
- `src/outlines/inputs.py`
- `src/outlines/caching.py`
- `src/outlines/exceptions.py`
- `src/outlines/types/`
- `src/outlines/backends/`
- `src/outlines/processors/`
- `src/outlines/models/`
- `docs/guide/`
- `docs/features/`
- `docs/examples/`
- `examples/`
- `tests/types/`
- `tests/backends/`
- `tests/models/`
- `tests/test_generator.py`
- `tests/test_templates.py`
- `tests/test_inputs.py`
- `tests/test_applications.py`
- `tests/test_cache.py`
- `tests/test_exceptions.py`

## Refresh guidance

Refresh this skill when any of the following change:

- Public loader functions in `src/outlines/models/`.
- `Generator`, `Application`, `Template`, `Chat`, `Image`, or output-type constructors.
- Backend defaults or compatibility in `src/outlines/backends/`.
- Provider exception normalization in `src/outlines/exceptions.py`.
- Supported optional dependencies in `pyproject.toml`.
- Documentation for supported model/provider/output-type matrices.
