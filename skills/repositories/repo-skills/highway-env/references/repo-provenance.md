# Repo provenance

This generated repo skill was distilled from the public Farama HighwayEnv repository and package evidence listed below.

## Source snapshot

- Package/distribution: `highway-env`
- Import package: `highway_env`
- Source package version: `1.12.1`
- Git commit: `07b824f9ba07074aa9591c53bd718ed1dba78514`
- Branch at generation: `main`
- Exact tag at generation: `v1.12.1`
- Remote URL: `https://github.com/Farama-Foundation/HighwayEnv.git`
- Working tree state at final generation: dirty because the generated `skills/` output and review artifacts were untracked. The package source directories used as evidence were not modified by this skill production.

## Evidence paths used

- `pyproject.toml`
- `setup.py`
- `README.md`
- `highway_env/__init__.py`
- `highway_env/envs/`
- `highway_env/envs/common/`
- `highway_env/road/`
- `highway_env/vehicle/`
- `highway_env/interval.py`
- `highway_env/utils.py`
- `docs/quickstart.md`
- `docs/environments/`
- `docs/actions/index.md`
- `docs/observations/index.md`
- `docs/rewards/index.md`
- `docs/graphics/index.md`
- `docs/multi_agent.md`
- `docs/make_your_own.md`
- `docs/dynamics/`
- `docs/faq.md`
- `docs/content/algorithms.md`
- `scripts/README.md`
- selected Python scripts under `scripts/`
- `tests/envs/`
- `tests/road/`
- `tests/vehicle/`
- `tests/graphics/`
- `tests/test_utils.py`
- `.github/workflows/build.yml`
- `Justfile`
- `CONTRIBUTING.md`

## Runtime inspection facts verified during creation

- `highway_env.__version__` reported `1.12.1`.
- Importing `highway_env` and calling `gym.register_envs(highway_env)` registered 31 HighwayEnv Gymnasium IDs.
- A bounded `highway-v0` reset/step smoke check succeeded.
- `render_mode="rgb_array"` produced an RGB frame with shape `(150, 600, 3)` in the inspection environment.
- `pip check` reported no broken requirements in the private inspection environment.

## Refresh triggers

Refresh this skill when any of the following change:

- the package version, registration list, or environment ID/version mapping;
- Gymnasium reset/step/render API compatibility;
- observation/action factory type names or key configuration parameters;
- reward/info keys for built-in environments;
- road, lane, vehicle, connected-lane neighbour, or custom-environment APIs;
- optional RL example compatibility guidance;
- installation dependencies, Python version support, or pygame/headless rendering behavior.

No private environment paths, local executable paths, or checkout-specific paths are required to use this runtime skill.
