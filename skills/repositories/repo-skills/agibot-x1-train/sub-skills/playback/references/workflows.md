# Playback Workflows

## Install And Import Contract

This route is intentionally conservative because playback depends on the
retired, vendor-distributed Isaac Gym Preview 4 binary stack.

1. Create a Python 3.8 environment.
2. Install the documented compute stack:

   ```bash
   conda install pytorch==1.13.1 torchvision==0.14.1 \
     torchaudio==0.13.1 pytorch-cuda=11.7 -c pytorch -c nvidia
   conda install numpy=1.23
   ```

3. Download Isaac Gym Preview 4 from NVIDIA, enter its `python/` directory, and
   install it editable:

   ```bash
   python -m pip install -e .
   ```

4. Run a vendor Isaac Gym example such as `1080_balls_of_solitude.py` from its
   examples directory. This is a backend prerequisite, not proof that X1
   playback passes.
5. From the X1 repository root, install the project editable:

   ```bash
   python -m pip install -e .
   ```

6. Ensure imports used transitively by playback are available:

   ```bash
   python -m pip install pygame wandb scipy
   ```

   The package metadata already names OpenCV, TensorBoard, NumPy, MuJoCo, and
   Isaac Gym, but the runtime imports `pygame`, `wandb`, and the terrain helper's
   `scipy`; these are not all declared by the package metadata. MuJoCo packages
   are not part of playback itself but may be installed by the repository's
   package metadata.
7. Validate in the actual target environment:

   ```bash
   python -c "from isaacgym import gymapi; import torch; import humanoid; import pygame, cv2, wandb; print(torch.__version__, torch.version.cuda)"
   ```

Importing only `torch` on CPU is not backend verification. Isaac Gym must be
imported and its native GPU example must run before interactive X1 playback.
Do not upgrade the documented versions casually: binary/API compatibility is
part of this workflow.

## Preflight First

The bundled helper is safe by default:

```bash
python scripts/playback_preflight.py \
  --repo-root /path/to/agibot_x1_train \
  --task x1_dh_stand \
  --experiment-name x1_dh_stand \
  --load-run 'RUN_DIRECTORY' \
  --checkpoint 1000 \
  --num-envs 1 \
  --require-joystick
```

It checks paths, module discoverability without importing modules, PyTorch/CUDA
metadata in an isolated subprocess, display variables, and Linux joystick
nodes. It does not load pickle data. Add `--json` for machine-readable output
or `--skip-backend-check` only for a filesystem-only audit. A skipped backend
check cannot clear `BLOCKED_REQUIRED_BACKEND`.

To select latest using repository defaults, omit both selection flags:

```bash
python scripts/playback_preflight.py --repo-root /path/to/agibot_x1_train
```

The helper prints the exact playback command it recommends but never executes
it.

## Playback Arguments

`play.py` uses the repository's shared `get_args()` parser. These are the exact
project-defined flags relevant to this route:

| Flag | Parser type/default | Playback effect |
|---|---|---|
| `--task` | string, parser default `XBotL_free` | Registry key. Override with exact `x1_dh_stand`; the parser default is not registered here. |
| `--resume` | boolean switch, default false | Unnecessary for playback because `play.py` sets runner resume true. |
| `--experiment_name` | optional string | Overrides `x1_dh_stand` and changes the checkpoint log root. |
| `--run_name` | optional string | Names a newly constructed playback log/video path; does not select a trained run. |
| `--load_run` | optional **string** | Trained run directory below `exported_data`; omission preserves configured integer `-1` (latest). |
| `--checkpoint` | optional integer | `N` means `model_N.pt`; `-1` means latest model candidate. |
| `--headless` | boolean switch | Disables viewer creation; not valid for this interactive route and unsafe with the unconditional camera call. |
| `--horovod` | boolean switch | Training/distribution option; no playback role. |
| `--rl_device` | string, default `cuda:0` | Device for runner and inference policy. |
| `--num_envs` | optional integer | Overrides environment count after the script's ten-env cap; use `1` initially. |
| `--seed` | optional integer | Can override environment seed during creation, although `play.py` separately sets training config seed to `123145`. |
| `--max_iterations` | optional integer | Runner config override with no role in the fixed playback loop. |

Isaac Gym's parser also supplies simulator flags such as `--sim_device`,
`--physics_engine`, pipeline/device options, and PhysX thread/subscene options.
Use `python humanoid/scripts/play.py --help` in the installed Preview 4
environment as the authority for those vendor-defined options. This skill does
not fabricate their availability without that backend. For the documented GPU
path, `--sim_device=cuda:0 --rl_device=cuda:0` is the normal pairing.

Both `--flag=value` and `--flag value` forms are accepted by the underlying
argument parser for value-taking flags.

## Model And Log Discovery

The configured X1 experiment name is `x1_dh_stand`. The code—not the README's
singular `/log` shorthand—loads from:

```text
<repository>/logs/<experiment_name>/exported_data/<load_run>/model_<checkpoint>.pt
```

Loading proceeds as follows:

1. `play.py` gets the registered environment and training configuration.
2. It forces `train_cfg.runner.resume = True`.
3. The registry creates `log_root` as
   `logs/<experiment_name>/exported_data`.
4. If effective `load_run == -1` (integer), entries in `log_root` are sorted
   lexicographically, an entry named exactly `exported` is removed, and the
   final entry is selected.
5. An explicit run is joined directly below `log_root`.
6. If `checkpoint == -1`, every filename containing substring `model` is
   collected, sorted by zero-left-padding the whole name to width 15, and the
   final candidate is selected.
7. Otherwise, the path is exactly `model_<checkpoint>.pt`.
8. The runner calls `torch.load(path)` and loads
   `loaded_dict["model_state_dict"]` with strict architecture matching. During
   playback optimizer states are not loaded.

Consequences:

- A literal CLI `--load_run=-1` is a string and therefore attempts directory
  `exported_data/-1`. Omit the flag for latest.
- Latest run selection is lexicographic, not modification-time based.
- Latest checkpoint selection is filename-based and does not require the
  strict `model_<integer>.pt` pattern. Keep only canonical checkpoint names in
  a run or select explicitly.
- An explicit checkpoint must exist; no nearest-number fallback occurs.
- A valid input is a full runner checkpoint dictionary. Exported JIT/ONNX
  actor files have a different contract and must go through the export or
  sim2sim routes.
- The loader has no `map_location`; use the compatible CUDA/PyTorch environment
  in which the checkpoint can be restored.

## Interactive Launch

Recommended first launch:

```bash
python humanoid/scripts/play.py \
  --task=x1_dh_stand \
  --load_run='RUN_DIRECTORY' \
  --checkpoint=1000 \
  --num_envs=1 \
  --rl_device=cuda:0 \
  --sim_device=cuda:0
```

Do not pass `--headless`. Do not confuse `--run_name` with `--load_run`.
Controller absence does not stop the script: the joystick open exception is
printed and command globals remain zero. For an intended joystick test, treat
that fallback as failure rather than successful interactive validation.

## What Playback Overrides

Before environment creation, `play.py` changes the registered configuration:

- starts from at most 10 environments, then CLI `--num_envs` may override it;
- forces plane terrain, 5 rows/columns, initial terrain level 5, and a
  1000-second episode;
- disables observation noise and its curriculum;
- disables friction, pushes, continuous pushes, base mass/COM, gains, torque,
  link mass, motor offset, joint friction/damping/armature, and one action-lag
  randomization switch;
- disables heading-command mode;
- sets training config seed to `123145`;
- forces resume and obtains deterministic inference actions with
  `get_inference_policy(device=env.device)`.

These are evaluation-time changes, not training implementation. They do not
prove that every lag/randomization feature is disabled; do not describe
playback as a fully deterministic physics benchmark.

## Viewer And Loop Lifecycle

Without `--headless`, environment construction creates an Isaac Gym viewer,
subscribes `Esc` to quit and `V` to viewer-sync toggle, and creates a camera
sensor. `play.py` then points the viewer camera at configured position/look-at.
Each `env.step(actions)` calls render, simulates ten physics steps per policy
step, computes new observations, and handles resets. With `dt=0.001` and
control decimation 10, the policy/control interval is 0.01 s (100 Hz), even
though a nearby config comment is ambiguous.

The playback loop runs `10 * stop_state_log = 10000` policy steps. State logging
is collected for part of the first 1000 steps. Optional video code exists but
`RENDER` is false by default; JIT export inside `play.py` also exists but
`EXPORT_POLICY` is false and is outside this route.

If a joystick opens, its polling thread is non-daemon, reads every 100 ms, and
has no normal shutdown assignment or `pygame.quit()` cleanup in the script.
See troubleshooting if the viewer closes but the Python process remains.

## Handoffs

- **From training:** receive the exact experiment name, run directory, and
  `model_N.pt`. Validate playback against that full checkpoint.
- **To export:** after model selection and architecture compatibility are
  established, pass the same task/run/checkpoint identity. Export owns JIT and
  ONNX production.
- **To sim2sim:** pass the exported policy artifact and MuJoCo contract, not the
  runner checkpoint and not the Isaac Gym viewer procedure.
