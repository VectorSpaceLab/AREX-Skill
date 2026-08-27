# Troubleshooting

## Install and import failures

- **`ModuleNotFoundError` for Isaac Lab packages**
  - Likely cause: the repo packages were not installed into the active Python environment.
  - Recovery: rerun `./isaaclab.sh -i` for the standard stack, or `./isaaclab.sh -i core` if you only need the core packages.
  - Confirm with `python -m pip check` and `python -I -c "import isaaclab, isaaclab_tasks, isaaclab_assets"`.

- **Dependency mismatch reported by `pip check`**
  - Likely cause: an optional extra pulled in a conflicting package version.
  - Recovery: install only the extra you actually need, then rerun the install command and `pip check`.

## Launcher and backend failures

- **`KeyError: 'EXP_PATH'` or missing Isaac Sim runtime files**
  - Likely cause: a Kit-based workflow was launched without the Isaac Sim environment being active.
  - Recovery: launch through `./isaaclab.sh` or source the Isaac Sim environment before running Kit-based scripts.

- **`--headless` behaving unexpectedly**
  - Likely cause: the launcher treats `--headless` as compatibility-only.
  - Recovery: omit `--viz` for the default headless path, or pass `--viz none` to disable all visualizers explicitly.

- **Kit visualizer used with OV backends**
  - Likely cause: `kit` visualizer and `ovphysx`/`ovrtx` are incompatible in the same process.
  - Recovery: use a kitless visualizer such as `newton`, `rerun`, or `viser`, or switch to a Kit-compatible backend.

## Preset and task failures

- **`Key 'physics' is not in struct`**
  - Likely cause: the script did not parse the typed preset tokens before handing the remainder to Hydra.
  - Recovery: make sure the script adds launcher args, calls `setup_preset_cli`, and passes the remainder through unchanged.

- **`Unknown preset(s)`**
  - Likely cause: the requested preset name is not defined for that task or the alias is outdated.
  - Recovery: use the bundled task preset helper to inspect valid names and switch to the canonical selector.

## RL failures

- **`No module named common` or similar when invoking training scripts directly**
  - Likely cause: the unified RL wrappers were not invoked through the repo command path.
  - Recovery: use `./isaaclab.sh train ...` or `./isaaclab.sh play ...`.

- **Distributed training on CPU**
  - Likely cause: the requested device is incompatible with distributed training.
  - Recovery: use a CUDA device for distributed runs.

## Teleop and imitation failures

- **Missing `robomimic`, `isaacteleop`, `dex-retargeting`, or `tomli`**
  - Likely cause: the optional imitation or teleop dependencies were not installed.
  - Recovery: install the relevant package or extra before retrying the workflow.

- **cuRobo / SkillGen setup crashes after sourcing Isaac Sim scripts**
  - Likely cause: the shell inherited Kit Python variables that shadow the target environment.
  - Recovery: install cuRobo from a clean shell, then source Isaac Lab or Isaac Sim again after installation.

## Tooling and maintenance failures

- **Docs or formatting hooks fail after editing generated files**
  - Likely cause: the change needs a style or docs refresh.
  - Recovery: rerun the formatting or docs command from the repo wrapper and review the produced diff.

- **Conversion utilities fail on missing file formats**
  - Likely cause: the helper expects a specific source format or optional dependency.
  - Recovery: confirm the file format, install the matching extra, and use the bundled command planner before retrying.
