# Repository Provenance

- Schema: `disco.repo-provenance.v1`

## Source snapshot

- Repository: IsaacLab
- Canonical skill id: `isaaclab`
- VCS: git
- Commit: `2e44ddb2e19536579140496023b5ccb060bc4152`
- Branch: `release/3.0.0-beta2`
- Exact tag: none recorded
- Repository version file: `3.0.0`
- Core extension metadata version: `6.1.17`
- Working tree state at generation: dirty only because the generated skill tree and integration artifacts were added during this run.

## Verified package facts

- Installed distribution versions during inspection:
  - `isaaclab` `6.1.17`
  - `isaaclab_assets` `0.3.5`
  - `isaaclab_contrib` `0.4.4`
  - `isaaclab_experimental` `0.0.7`
  - `isaaclab_mimic` `1.3.4`
  - `isaaclab_newton` `0.13.6`
  - `isaaclab_ov` `0.4.2`
  - `isaaclab_ovphysx` `3.0.2`
  - `isaaclab_physx` `1.1.3`
  - `isaaclab_ppisp` `0.2.0`
  - `isaaclab_rl` `0.5.7`
  - `isaaclab_tasks` `1.10.9`
  - `isaaclab_tasks_experimental` `0.0.1`
  - `isaaclab_teleop` `0.5.2`
  - `isaaclab_visualizers` `0.1.0`
- Runtime checks that succeeded:
  - `import isaaclab`, `import isaaclab_tasks`, `import isaaclab_assets`, `import isaaclab_rl`
  - CUDA PyTorch availability on the host GPU stack
- Additional inspection note: `python -m pip check` was exercised during environment preparation, and optional teleop/mimic extras still report missing companion packages unless those optional dependencies are installed together.

## Evidence used

Relative evidence paths consulted during extraction:

- `README.md`
- `VERSION`
- `pyproject.toml`
- `docs/source/setup/installation/index.rst`
- `docs/source/setup/installation/kitless_installation.rst`
- `docs/source/overview/core-concepts/multi_backend_architecture.rst`
- `docs/source/overview/reinforcement-learning/rl_existing_scripts.rst`
- `docs/source/overview/imitation-learning/teleop_imitation.rst`
- `docs/source/overview/imitation-learning/skillgen.rst`
- `source/isaaclab/setup.py`
- `source/isaaclab_tasks/setup.py`
- `source/isaaclab_rl/setup.py`
- `source/isaaclab_mimic/setup.py`
- `source/isaaclab_teleop/setup.py`
- `source/isaaclab_visualizers/setup.py`
- `source/isaaclab_tasks/isaaclab_tasks/utils/preset_cli.py`
- `source/isaaclab_tasks/isaaclab_tasks/utils/preset_target.py`
- `source/isaaclab_tasks/isaaclab_tasks/utils/sim_launcher.py`
- `source/isaaclab/isaaclab/app/app_launcher.py`
- `source/isaaclab_assets/isaaclab_assets/__init__.pyi`
- `source/isaaclab/test/test_scripts_torcharray_patterns.py`
- `source/isaaclab_tasks/test/test_preset_cli.py`
- `source/isaaclab_tasks/test/test_env_cfg_no_forbidden_imports.py`
- `scripts/reinforcement_learning/test/test_typed_preset_cli_train_play.py`

## Excluded or de-prioritized paths

- VCS internals, caches, build outputs, and review artifacts.
- Heavy runtime-only scripts and hardware-specific workflows that are now routed to bundled references instead of being linked directly.

## Refresh triggers

Refresh this skill if the package versions, install tokens, CLI flags, backend compatibility rules, preset grammar, or task catalog change materially.
