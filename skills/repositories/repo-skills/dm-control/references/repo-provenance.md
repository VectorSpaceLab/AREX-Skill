# dm_control repo provenance

schema: `disco.repo-provenance.v1`

## Source identity

- Public repository: `https://github.com/google-deepmind/dm_control.git`
- Package/distribution name: `dm_control`
- Package version in source metadata: `1.0.44`
- Baseline commit: `985d09401ea8824cec489e56cd631b24d9e32891`
- Baseline branch: `main`
- Exact tag: none detected at baseline
- Source license: Apache-2.0

## Dirty-state note

The source checkout had generated `skills/` files during this skill-production run. No package-source modifications were used as evidence beyond the committed repository content and generated review/runtime artifacts.

## Evidence paths used

Package and setup evidence:

- `README.md`
- `pyproject.toml`
- `setup.py`
- `requirements.txt`
- `migration_guide_1.0.md`

Core package evidence:

- `dm_control/suite/`
- `dm_control/rl/control.py`
- `dm_control/mjcf/`
- `dm_control/mujoco/`
- `dm_control/composer/`
- `dm_control/entities/`
- `dm_control/utils/`
- `dm_control/manipulation/`
- `dm_control/locomotion/`
- `dm_control/viewer/`
- `dm_control/_render/`
- `dm_control/blender/mujoco_exporter/`

Examples, tutorials, and tests used as evidence:

- `tutorial.ipynb`
- `dm_control/mujoco/tutorial.ipynb`
- `dm_control/suite/explore.py`
- `dm_control/manipulation/explore.py`
- `dm_control/locomotion/examples/`
- `dm_control/locomotion/soccer/explore.py`
- Representative `*_test.py` files under the package source tree

## Installed-package verification baseline

The construction process installed the package non-editably and verified:

- `dm_control` imported as version `1.0.44`.
- `dm_control.suite`, `dm_control.mjcf`, `dm_control.mujoco`, `dm_control.composer`, and `dm_control.manipulation` imported successfully.
- `suite.ALL_TASKS` exposed 51 tasks and `suite.BENCHMARKING` exposed 28 tasks.
- `manipulation.ALL` exposed 25 tasks with tags `features`, `vision`, and `easy`.
- A CPU `cartpole/balance` reset/step smoke passed.
- A tiny PyMJCF model compiled and stepped.
- An EGL render probe produced a frame in the construction environment; OSMesa and GLFW were unavailable there due to system/display constraints and remain optional backend concerns.

This generated skill is self-contained runtime guidance. Future agents should refresh it if the package version, public APIs, task registries, install constraints, or rendering backend behavior changes materially.
