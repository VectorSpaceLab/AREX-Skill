# Repo Provenance

## Source Snapshot

- Repository: Tianshou
- Package name: `tianshou`
- Package version: `2.0.1`
- Source commit: `f2402056b03acafeedf2518a5088db55add004ab`
- Branch: `master`
- Exact tag: none recorded at the source commit
- Remote URL: `https://github.com/thu-ml/tianshou`
- Working tree state at generation: dirty due to generated `skills/` output

## Evidence Paths

The skill was generated from these repository-relative evidence paths:

- `pyproject.toml`
- `README.md`
- `CHANGELOG.md`
- `tianshou/`
- `docs/01_user_guide/`
- `docs/02_deep_dives/`
- `docs/04_benchmarks/`
- `docs/05_developer_guide/`
- `examples/discrete/`
- `examples/mujoco/`
- `examples/atari/`
- `examples/offline/`
- `examples/inverse/`
- `examples/modelbased/`
- `examples/vizdoom/`
- `examples/box2d/`
- `benchmark/run_benchmark.py`
- `test/base/`
- `test/highlevel/`
- `test/discrete/`
- `test/continuous/`
- `test/offline/`
- `test/modelbased/`
- `test/pettingzoo/`

## Excluded Evidence

The following were not used as runtime dependencies:

- `.git/`, `.github/`, `.devcontainer/`, and release/CI/dev infrastructure
- generated/static documentation assets under `docs/_static/`
- docs maintainer utilities such as `docs/autogen_rst.py`, `docs/create_toc.py`, and `docs/nbstripout.py`
- binary/game assets such as VizDoom WAD files
- build/cache/local-environment directories
- DisCo review/test artifact directories

## Installed-Package Inspection Baseline

Live inspection verified `tianshou` imports, package metadata, high-level APIs, procedural algorithm APIs, data/env APIs, and offline/specialized imports against version `2.0.1`. Optional Atari, Box2D, MuJoCo, VizDoom, EnvPool, robotics, Ray, D4RL, and broad dev dependencies were intentionally not treated as default requirements.
