# RL troubleshooting

Use this page for PPO training/playback failures around `HoverAviary`, `MultiHoverAviary`, Gymnasium registration, SB3 imports, saved model paths, results folders, plotting, and headless operation.

## Missing or incompatible RL imports

Typical symptoms:

```text
ModuleNotFoundError: No module named 'gymnasium'
ModuleNotFoundError: No module named 'stable_baselines3'
ModuleNotFoundError: No module named 'torch'
ImportError or pip check failures after installing pybullet/torch/SB3
```

Recovery:

1. Confirm you are in the intended Python 3.12 environment.
2. Install the package dependencies in that same environment. For a local source tree, the project evidence uses:

   ```bash
   python -m pip install -e /path/to/gym-pybullet-drones
   python -m pip check
   ```

3. Run the helper preflight:

   ```bash
   python scripts/run_rl_workflow.py check-imports
   ```

4. If `torch` installs but SB3 fails, check that `stable-baselines3` and `gymnasium` versions are compatible with the installed Python and torch build. The project metadata targets `stable-baselines3` 2.x/2.9-era and `gymnasium` 1.x/1.3-era dependencies.
5. Avoid mixing a system Python invocation with a Conda/venv where dependencies were installed.

## Gymnasium env ID is missing

Symptom:

```text
gymnasium.error.NameNotFound: Environment `hover-aviary` doesn't exist
```

Recovery:

- Import `gym_pybullet_drones` before calling `gym.spec(...)` or `gym.make(...)`; registration lives in `gym_pybullet_drones/__init__.py`.
- Use exact IDs: `hover-aviary-v0` and `multihover-aviary-v0`.
- If the IDs are still missing, reinstall the package in the active environment and rerun `check-imports`.

## Playback model path is missing or wrong

Symptoms:

```text
[ERROR] Model file not found at: results/best_model.zip
Model path does not exist: ...
FileNotFoundError while PPO.load(...)
```

Recovery:

1. Do not assume the source placeholder `results/best_model.zip` exists.
2. Use the concrete path printed by training, usually:

   ```text
   <output-folder>/save-<timestamp>/best_model.zip
   <output-folder>/save-<timestamp>/final_model.zip
   ```

3. If you trained with the bundled helper, inspect `rl_workflow_summary.json` for `best_model_path` and `final_model_path`.
4. If you trained with the source `learn.py`, use the README pattern from the examples directory: pick the latest timestamped folder under `results/` and pass `results/<latest>/best_model.zip`.
5. The bundled helper exits non-zero on a missing path so automation can fail early with an actionable message.

## Torch / CUDA auto-selection warnings

On hosts with a CUDA-capable Torch install, SB3 may automatically select the GPU for `PPO('MlpPolicy', ...)` even though this workflow does not require CUDA. A warning about MLP policies on GPU is usually not fatal for the smoke run.

Recovery:

- Treat the warning as optional-capability noise, not a blocker, if the command exits `0`.
- If you want to force CPU-only execution for a local smoke run, adjust the helper or set the appropriate Torch/ CUDA visibility in your shell before launching the script.
- Do not claim a required GPU backend for this package; the selected native RL workflow is CPU-valid.

## Short smoke mode vs full training confusion

Symptoms:

- Training unexpectedly runs for a very long time.
- A future agent says it used `local=True` for a quick test.
- Smoke training does not learn a useful policy, but the model file loads.

Recovery:

- Source `learn.run(local=False)` is the CI-style short branch (`int(1e2)` timesteps, with SB3 rollout behavior still adding overhead).
- Source `learn.run(local=True)` is the full branch (`int(1e7)` timesteps). Do not use it accidentally.
- The bundled helper defaults to explicit short `--timesteps`; increase it only when the user asks for real training and a runtime budget exists.
- A smoke run verifies imports, env construction, PPO rollout, save/load, and playback mechanics. It does not prove a high-quality hover policy.

## Results folder and artifact layout problems

Symptoms:

- No `best_model.zip` after a failed or interrupted run.
- Output folder is missing or not writable.
- Multiple timestamped `save-*` folders make it unclear which model to play.

Recovery:

- Use an absolute or temporary `--output-folder` for automation, e.g. `/tmp/drones-rl-smoke`.
- The helper creates folders before training and writes `rl_workflow_summary.json` with exact model paths.
- If a run was interrupted before saving, do not pass its incomplete folder to playback; rerun a short smoke or use an earlier complete `best_model.zip`/`final_model.zip`.
- Keep train and playback logs in separate folders when comparing single-agent and multi-agent runs.

## Plotting and display failures

Symptoms:

```text
Failed to create and OpenGL context
cannot connect to X server
Matplotlib backend/display errors
PyBullet GUI opens during automation
```

Recovery:

- Run smoke training and playback with `gui=False`; the helper defaults headless and only enables GUI when `--gui` is passed.
- Leave `--plot` off in CI/headless sessions. Plotting can require a display depending on Matplotlib backend.
- If a GUI is required on a remote machine, set up display forwarding or a virtual framebuffer before enabling `--gui`.
- Do not use GUI as part of the required verification gate; use headless playback first.

## Single-agent vs multi-agent configuration mismatch

Symptoms:

- A model trained with `HoverAviary` fails or behaves incorrectly when played with `MultiHoverAviary`.
- Action/observation shapes differ from expectations.
- `num_drones` differs between training and playback.

Recovery:

- Keep `--multiagent` and `--num-drones` identical between training and playback.
- Single-agent: `HoverAviary`, env ID `hover-aviary-v0`, one drone.
- Multi-agent: `MultiHoverAviary`, env ID `multihover-aviary-v0`, default two drones.
- Multi-hover is a joint Gymnasium Box environment; do not route it as independent per-agent policies unless you write a separate wrapper.

## Action/observation option mismatch

Symptoms:

- SB3 shape errors during `model.predict` or `env.step`.
- Logger reports invalid state length.
- A model trained with one action type is played with another.

Recovery:

- Use the same `--obs` and `--act` values for train and play.
- Default source and helper choices are `kin` observations and `one_d_rpm` actions.
- `BaseRLAviary` action dimensions differ by action type: `rpm`/`vel` are 4D, `pid` is 3D, and `one_d_rpm`/`one_d_pid` are 1D.
- The source logger examples fit the default `kin` + `one_d_rpm` layout best. For other action types, disable plotting/log assertions unless you adapt the state packing.

## PyBullet cleanup and interrupted runs

Symptoms:

- Later PyBullet runs fail after a crashed script.
- The process hangs around GUI or render calls.

Recovery:

- Always close environments with `env.close()`; the helper does this in `finally`-style paths.
- Prefer one short smoke process per workflow when diagnosing crashes.
- If GUI was enabled and PyBullet is stuck, stop the Python process and rerun headless.
