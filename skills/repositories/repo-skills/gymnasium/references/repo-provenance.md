# Gymnasium Repo Provenance

Schema: `disco.repo-provenance.v1`

This repo skill was generated from the Gymnasium repository state below. Use this file to decide whether the skill should be refreshed after source changes.

## Source Snapshot

| Field | Value |
| --- | --- |
| Repository | Farama-Foundation/Gymnasium |
| Remote URL | https://github.com/Farama-Foundation/Gymnasium.git |
| Branch | main |
| Commit | eff2884820b7b5af7376aa2b1e5d40fb1feaf547 |
| Exact tag | none |
| Package distribution | gymnasium |
| Package version | 1.3.0 |
| Python support in metadata | >=3.10 |
| Working tree state | dirty: generated `skills/` content was untracked during skill creation |

## Primary Evidence Paths

- `README.md`
- `pyproject.toml`
- `setup.py`
- `gymnasium/__init__.py`
- `gymnasium/core.py`
- `gymnasium/envs/registration.py`
- `gymnasium/envs/`
- `gymnasium/spaces/`
- `gymnasium/wrappers/`
- `gymnasium/vector/`
- `gymnasium/utils/`
- `docs/api/`
- `docs/introduction/`
- `docs/tutorials/gymnasium_basics/`
- `docs/tutorials/training_agents/`
- `docs/environments/`
- `tests/envs/`
- `tests/spaces/`
- `tests/wrappers/`
- `tests/vector/`
- `tests/utils/`

## Scope Notes

Generated runtime guidance covers public Gymnasium use: environment loops, custom envs, registration, spaces, wrappers, recording, vectorization, built-in environment families, optional extras, and Gym migration.

The skill intentionally excludes maintainer-only CI/release infrastructure, documentation generation scripts, generated media assets, broad optional backend installation, and long training examples as runtime dependencies. Long tutorials and tests were used as evidence or verification candidates, not as files that future agents must open from the original repository.
