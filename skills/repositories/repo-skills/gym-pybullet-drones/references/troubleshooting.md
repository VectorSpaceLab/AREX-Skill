# gym-pybullet-drones Troubleshooting

## When to read

Read this for cross-workflow installation, import, Gymnasium registration, headless/GUI, output, and bundled-helper issues. For workflow-specific failures, route to the nearest sub-skill troubleshooting file.

## Install or import fails

Typical symptoms:

```text
ModuleNotFoundError: No module named 'gym_pybullet_drones'
ModuleNotFoundError: No module named 'pybullet'
ImportError while importing gym_pybullet_drones.envs
pip check reports broken dependencies
```

Actions:

1. Use a clean Python 3.12 environment for this package baseline.
2. Install the package and dependencies in that same environment:

   ```bash
   python -m pip install gym-pybullet-drones
   # or for a local checkout:
   python -m pip install -e /path/to/gym-pybullet-drones
   python -m pip check
   ```

3. Run the bundled import check from the generated skill root:

   ```bash
   python scripts/check_imports.py
   python scripts/check_imports.py --headless-smoke --env-id hover-aviary-v0
   ```

4. Do not mix a system Python command with a Conda/venv where the package was installed.
5. If `pybullet` builds from source, confirm a compiler/build toolchain is present. If a wheel exists for the platform, prefer the wheel path.

## Gymnasium env ID is not found

Symptom:

```text
gymnasium.error.NameNotFound: Environment `hover-aviary` doesn't exist
```

Actions:

- Import `gym_pybullet_drones` before `gym.spec(...)` or `gym.make(...)`; registration is performed in the package import.
- Use exact IDs: `ctrl-aviary-v0`, `velocity-aviary-v0`, `hover-aviary-v0`, and `multihover-aviary-v0`.
- Reinstall the package if `scripts/check_imports.py` shows missing IDs after import.

## GUI, display, and OpenGL failures

Typical symptoms:

```text
Failed to create an OpenGL context
cannot connect to X server
PyBullet hangs when gui=True
Matplotlib backend/display errors
```

Actions:

- Run smoke checks with `gui=False`, `--no-gui`, and `--no-plot` first.
- Enable GUI only on a host with a working X/Wayland/display-forwarding setup and OpenGL.
- Keep plotting disabled until the simulation or RL workflow runs headless.
- If recording headless, expect PNG frames; convert them later with `scripts/ffmpeg_png2mp4.sh` if `ffmpeg` is available.

## CPU, Torch, and accelerator confusion

The package's selected workflows do not require CUDA, ROCm, MPS, or a vendor accelerator. PyBullet simulation and the native smoke tests run on CPU/generic Python. Torch may use CUDA in a user's environment, but that is not a required gate for this skill.

If Torch or SB3 import fails:

1. Route RL-specific issues to `sub-skills/rl-workflows/references/troubleshooting.md`.
2. Confirm the active Python environment has compatible `torch`, `gymnasium`, and `stable-baselines3` versions.
3. If a CUDA-enabled Torch wheel is incompatible with the host, use an evidence-backed CPU or compatible CUDA wheel; do not treat CUDA setup as part of the PyBullet control workflow.

## Gymnasium passive-checker warnings during smoke tests

The current package can emit Gymnasium warnings about `Box` precision, reset/step observation dtype, or observations being outside the declared space during quick smoke runs. Treat these as compatibility warnings when the command exits `0`; they are useful source-maintenance signals but should not block an operating smoke check by themselves.

If a task is specifically to fix those warnings in source code, route it as repository maintenance rather than package operation.

## Timing, action shape, and state-vector failures

Cross-cutting rules:

- `BaseAviary` requires `pyb_freq % ctrl_freq == 0`.
- Control observations are `(num_drones, 20)` arrays containing position, quaternion, RPY, velocities, angular velocities, and last RPMs.
- `Logger.log(...)` expects a single 20-value state vector and one 12-value control vector per drone.
- Use the bundled control runner to prevalidate timing and model choices before constructing a PyBullet environment.

Route detailed control issues to `sub-skills/control-simulation/references/troubleshooting.md`.

## Betaflight SITL prerequisites are missing

Symptoms:

```text
betaflight_sitl/bf0 not found: run assets/clone_bfs.sh ... first
FileNotFoundError for betaflight_SITL.elf
UDP port timeout or no PWM packets
```

Actions:

- Route to `sub-skills/betaflight-sitl/SKILL.md`.
- Run the safe layout checker before executing any SITL workflow:

  ```bash
  python sub-skills/betaflight-sitl/scripts/check_betaflight_layout.py --num-drones 2
  ```

- Do not bundle or auto-run the source `clone_bfs.sh` logic from this skill; it clones and patches an external repository and depends on host build tools.

## Video conversion fails

The original package contains a small FFmpeg helper for PNG frame conversion; this skill bundles an adapted copy at `scripts/ffmpeg_png2mp4.sh`.

Actions:

```bash
bash scripts/ffmpeg_png2mp4.sh --help
bash scripts/ffmpeg_png2mp4.sh --input-pattern '/tmp/recording/frame_%d.png' --output-file /tmp/video.mp4
```

If conversion fails, confirm:

- `ffmpeg` is installed and on `PATH`.
- Frame names match the input pattern, usually `frame_0.png`, `frame_1.png`, ...
- Resolution and frame rate match the saved frames.
- The output file does not already exist unless you pass `--force`.

## A task asks for source examples or tests

For operating use, do not tell future agents to run source checkout paths such as `gym_pybullet_drones/examples/pid.py`. Use bundled helpers instead:

- `sub-skills/control-simulation/scripts/run_control_example.py`
- `sub-skills/rl-workflows/scripts/run_rl_workflow.py`
- `sub-skills/betaflight-sitl/scripts/check_betaflight_layout.py`

Original repository tests are verification evidence, not runtime dependencies for this generated skill.
