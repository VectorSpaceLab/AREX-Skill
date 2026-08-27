# Setup And Configuration Troubleshooting

Use this page when setup, imports, config composition, or data checks fail before a Habitat environment, trainer, or HITL app is running.

## `ModuleNotFoundError: No module named 'magnum'`

Likely cause: `habitat-sim` is missing or was installed for an incompatible Python/platform combination. Habitat-Lab imports may transitively require `magnum` even when the immediate user code only imports `habitat`.

Actions:

1. Confirm Python version and environment activation.
2. Prefer a Python 3.9 conda environment for Habitat-Lab `0.3.x` public install compatibility.
3. Install Habitat-Sim from conda with the needed physics variant, for example `conda install habitat-sim withbullet -c conda-forge -c aihabitat`.
4. Re-run `python -c "import habitat_sim, magnum"` before retrying `import habitat`.
5. If Python is newer and no compatible Habitat-Sim package exists, create a compatible environment instead of patching Habitat-Lab code.

## `ModuleNotFoundError: No module named 'habitat_sim'`

Likely cause: core `habitat-lab` installed without the simulator dependency, wrong environment is active, or `habitat-sim` install failed.

Actions:

1. Run `python -c "import sys; print(sys.executable); import habitat_sim"` in the same shell used by the failing command.
2. Install or repair `habitat-sim` before debugging datasets/configs.
3. For rearrangement/physics configs, ensure the install includes Bullet support.
4. If using containers or remote machines, verify that the command is running inside the prepared environment, not the host Python.

## Python Version Mismatch

Symptoms:

- `habitat-lab` appears installed but `import habitat` fails on `magnum` or `habitat_sim`.
- `pip` can install pure Python packages, but no matching native simulator package is available.
- Import failures disappear in Python 3.9 but not in newer Python.

Actions:

- Treat `habitat-sim` package availability as the deciding compatibility constraint.
- Prefer Python 3.9 for a reliable public Habitat-Lab `0.3.x` setup.
- Do not assume package metadata classifiers alone prove simulator compatibility.
- Recreate the environment when native dependency conflicts accumulate.

## Gym Deprecation Warning

Symptom: importing or running Habitat emits a warning that Gym is unmaintained or suggests Gymnasium.

Likely cause: Habitat-Lab `0.3.x` depends on Gym `>=0.22,<0.23.1`. This warning can appear even when setup is otherwise correct.

Actions:

- Do not treat the warning alone as a setup failure.
- Keep the pinned Gym range unless the user is intentionally porting code.
- Investigate only if a concrete Gym API error follows the warning.

## Hydra Cannot Find Config

Common symptoms:

- `RuntimeError: No file found for config ...`
- `MissingConfigException`
- A baselines command cannot locate a config that exists in the core Habitat config tree, or vice versa.

Actions:

1. Confirm which loader is being used:
   - `habitat.get_config(...)` resolves against the installed core Habitat config package by default.
   - `habitat_baselines.config.default.get_config(...)` resolves against installed baselines configs by default and registers baselines config groups.
2. Pass paths relative to the correct config root, such as `benchmark/nav/pointnav/pointnav_habitat_test.yaml` for core configs or `pointnav/ppo_pointnav_example.yaml` for baselines configs.
3. If using a custom YAML outside the package, pass the file path directly or use the `configs_dir` argument intentionally.
4. Use `scripts/config_probe.py --kind habitat|baselines --config ...` to isolate composition from runtime.

## Invalid Override Key Or Type

Common symptoms:

- Hydra/OmegaConf reports `Key not in struct`, `ConfigAttributeError`, or an unknown override.
- Override values compose but later fail type validation.
- A key name copied from old YACS configs does not work.

Actions:

1. Use lowercase Hydra keys under `habitat`, for example `habitat.environment.max_episode_steps`, not older uppercase/YACS names.
2. Use renamed keys from the Hydra config system: `agent.sim_sensors` instead of `agent.sensors`, and `task.lab_sensors` instead of `task.sensors`.
3. For baselines keys, use the `habitat_baselines` namespace, for example `habitat_baselines.evaluate=True`.
4. Quote shell-sensitive override values if they include brackets, commas, braces, spaces, or glob characters.
5. Compose with `config_probe.py` and print the exact target key to verify the path exists.
6. If a new key must be added dynamically in Python, use `read_write(config)`; for production configs prefer defining the key in structured config or the relevant YAML.

## Missing Dataset Or Scene Assets

Common symptoms:

- `FileNotFoundError` for `data/datasets/...` or `data/scene_datasets/...`.
- Config composition succeeds, but Env creation fails when loading episodes or scenes.
- `habitat.dataset.data_path` contains `{split}` and the resolved file is absent.

Actions:

1. Compose the config and inspect `habitat.dataset.split`, `habitat.dataset.data_path`, `habitat.dataset.scenes_dir`, and `habitat.simulator.scene`.
2. Launch from a directory where relative `data/...` paths exist, or override paths to the user's dataset root.
3. Download small smoke assets with Habitat-Sim dataset downloader for test-scene workflows.
4. Do not use HM3D/MP3D/Gibson/HSSD configs unless those large external datasets are actually present and licensed for the user.
5. For rearrangement configs, also check robot URDFs, scene instance configs, PDDL/task-spec paths, and physics config files.

## Baselines CLI Rejects Old Flags

Symptom: `habitat_baselines.run` raises a message saying `--exp-config` or `--run-type` has changed.

Actions:

- Replace `--exp-config` with `--config-name=<path-inside-baselines-config>`.
- Replace `--run-type train` with `habitat_baselines.evaluate=False`.
- Replace `--run-type eval` with `habitat_baselines.evaluate=True`.
- Route actual training/evaluation execution details to `../baselines-training-and-evaluation/SKILL.md`.

## Graphics, EGL, Or Magnum Runtime Warnings

Common symptoms:

- `Platform::WindowlessEglApplication::tryCreateContext(): unable to find CUDA device ... among ... EGL devices`
- `WindowlessContext: Unable to create windowless context`
- Magnum/EGL warnings during import or first simulator creation.
- Black rendered frames or black rectangles on specific NVIDIA GPUs.

Actions:

1. Separate import/config checks from rendering checks. `config_probe.py` does not create a simulator context.
2. Increase logs when debugging rendering: `HABITAT_SIM_LOG=Debug`, `MAGNUM_LOG=verbose`, and optionally `MAGNUM_GPU_VALIDATION=ON`.
3. On Linux, verify `nvidia-smi`, CUDA driver version, `eglinfo`, and `libglvnd`/EGL vendor configuration.
4. Try a minimal Habitat-Sim viewer with a known test scene before blaming Habitat-Lab task code.
5. If using A100 GPUs with black artifacts, update NVIDIA drivers to a recent CUDA 12.2+ capable driver.
6. For headless or CPU-only machines, choose configs that do not require rendering, or use an environment with a supported rendering backend.

## Interactive Display Errors

Symptom: interactive play or UI code fails with `X Error of failed request: BadAccess (attempt to access private resource denied)`.

Actions:

- Treat this as an interactive/display stack problem, not a config composition problem.
- Verify non-interactive import and config composition first.
- Route HITL and interactive application launch/debugging to `../hitl-apps-and-interaction/SKILL.md`.

## VectorEnv Hangs Or Silenced Errors During Debugging

Symptom: vectorized environment startup hangs or worker errors are hard to read.

Actions:

- Set `HABITAT_ENV_DEBUG=1` while debugging to use the slower, more verbose threaded vector environment path.
- Unset `HABITAT_ENV_DEBUG` after debugging because the normal vectorized path is faster.
- Route post-setup Env behavior to `../tasks-datasets-and-envs/SKILL.md`.

## Quick Isolation Matrix

- Import fails: fix Python/Habitat-Sim/package installation first.
- Config composition fails: fix config path, config group, or override syntax.
- Config composes but `--check-paths` fails: fix working directory, `data/` symlink, dataset download, or path overrides.
- Env creation fails after imports/config/data pass: route to task/dataset/env runtime diagnostics.
- Baselines trainer launch fails after config pass: route to baselines training/evaluation diagnostics.
- HITL app display/client fails after imports/config pass: route to HITL diagnostics.
