# Playback Troubleshooting

Fail closed: do not open a viewer until static model selection, backend, display,
and controller intent are clear.

## Symptom Matrix

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: isaacgym` | Preview 4 absent or wrong environment | Install the vendor Preview 4 package into Python 3.8 and pass a vendor example. A generic simulator package is not a substitute. |
| Isaac Gym native extension/ABI error | Unsupported Python, PyTorch, CUDA, driver, or library path | Return to the documented Python 3.8, PyTorch 1.13.1, CUDA 11.7 stack; validate the vendor example before this repo. |
| `ModuleNotFoundError: pygame` | Undeclared playback import missing | Install `pygame` in the same environment. |
| `ModuleNotFoundError: wandb` | Runner imports an undeclared package | Install `wandb` even though playback does not start a W&B run. |
| Task lookup fails (`KeyError`/not registered) | Parser default or typo used | Pass exact `--task=x1_dh_stand`. The parser default `XBotL_free` is not the registered task here. |
| `No runs in this directory` | Wrong experiment or missing `exported_data` | Verify `logs/<experiment>/exported_data`; pass matching `--experiment_name` only if training used another experiment. |
| Run path ends in `/-1` | Literal `--load_run=-1` became a string | Omit `--load_run` to select latest, or pass the exact run directory name. |
| Latest run is unexpected | Selection is lexicographic | Pass explicit `--load_run`; do not assume modification-time ordering. |
| Empty model candidate error / index failure | Run has no filename containing `model` | Confirm training produced `model_N.pt`; select a complete run. |
| `model_N.pt` not found | Explicit checkpoint absent | List canonical checkpoint suffixes and choose an existing integer; there is no nearest fallback. |
| `torch.load` or unpickling error | Corrupt/untrusted/wrong artifact | Do not deserialize untrusted checkpoints. Recopy a known full runner checkpoint; do not use JIT/ONNX here. |
| Missing/unexpected state-dict keys or tensor size mismatch | Checkpoint architecture does not match X1 config | Require 66×47 actor input history, 12 actions, and matching `ActorCriticDH`; return to training/export provenance. |
| CUDA device error or tensors on wrong device | `rl_device`, `sim_device`, checkpoint, and available GPU disagree | Start with both devices on `cuda:0`; validate CUDA in the Preview 4 environment. CPU-only success is not an Isaac Gym playback result. |
| Viewer creation fails / black window | No display, invalid graphics device, remote GL issue, or driver mismatch | Check `DISPLAY`/`WAYLAND_DISPLAY`, local/X-forwarded graphics, NVIDIA driver, and vendor examples. Do not add `--headless` to claim interactive success. |
| `--headless` crashes around camera | Playback calls camera setup unconditionally after environment creation | Remove `--headless` for this route and repair the display/backend. |
| Viewer is open but frozen | Viewer sync toggled or simulation/backend blocked | Press `V` once, inspect terminal errors, and verify GPU utilization; `V` toggles synchronized drawing. |
| Viewer exits but process remains | Non-daemon joystick thread never receives its exit flag | Interrupt from the launching terminal; if maintaining the code, add a `try/finally` that sets the flag, joins the thread, and calls `pygame.quit()`. Do not leave orphaned processes. |
| Controller open failure message | pygame joystick index 0 unavailable or permission denied | Verify device node, permissions, F710 mode/receiver, and pygame enumeration. Zero-command viewer fallback is not joystick validation. |
| Robot moves without button 4 | Button gate exists only in documentation | This is current behavior: axes are always applied. Center sticks; implement/test a real dead-man gate before relying on it. |
| Drift at centered sticks | No software deadzone | Calibrate/diagnose raw axes; use small, explicit deadzone logic only after review and test. |
| Lateral/yaw response is too aggressive | Raw `[-1,1]` exceeds trained y/yaw ranges | Use small deflections; add reviewed clipping/scaling if modifying playback. |
| Direction or axis is wrong | OS/driver/F710 mode changed pygame numbering | Inspect raw axes before simulation; expected indices are x=1, y=0, yaw=3, all negated. |
| Policy shape error around `view`/linear layer | Observation history is not 3102 values | Preserve environment-managed 66×47 history. Do not pass a single frame. |
| First response seems delayed/mismatched | Action is computed before current loop command assignment | Expect a later-iteration effect; the first action uses initialized observation history. |

## Model Discovery Audit

Use the helper rather than guessing:

```bash
python scripts/playback_preflight.py \
  --repo-root /path/to/agibot_x1_train \
  --experiment-name x1_dh_stand \
  --load-run RUN_DIRECTORY \
  --checkpoint 1000 \
  --json
```

Review `selected_run`, `selected_model`, and every `ERROR`/`WARNING`. The helper
rejects unsafe absolute or parent-traversing run names even though raw path
joining in the project is less defensive. It intentionally does not call
`torch.load`, because PyTorch checkpoints are pickle-bearing artifacts.

For latest selection, run once without `--load-run`/`--checkpoint`, record what
was chosen, then rerun with those exact explicit values before interactive
playback. This avoids changes if another run/checkpoint appears between audit
and launch.

## Viewer Recovery

1. Stop playback; do not repeatedly retry a failing graphics process.
2. Run the Isaac Gym vendor example in the same shell/environment/GPU/display.
3. Confirm display variables and that the graphics device corresponds to a
   usable NVIDIA GPU.
4. Use one environment and the default visible viewer.
5. Keep optional in-script video (`RENDER`) disabled while isolating viewer
   problems. OpenCV/video sensor rendering is a separate failure surface.
6. Press `Esc` to request quit and verify the Python process exits. If a
   controller was opened, check for the thread-lifecycle issue above.

## Joystick Recovery

If command behavior is unsafe, release/center the sticks and terminate
playback. Button 4 is not an implemented stop control. Diagnose controller
values outside Isaac Gym. Confirm:

- pygame sees the intended device as joystick index 0;
- it has at least four axes;
- axes 0, 1, and 3 rest near zero;
- each expected physical stick moves only the intended raw axis;
- F710 mode changes have not altered numbering;
- motion signs agree with the bundled mapping.

Only then reopen playback with one environment.

## Escalation Records

When handing a failure to training, export, or environment maintainers, include:

- task and experiment;
- exact run directory and checkpoint filename;
- Python, PyTorch, CUDA runtime, driver, and Isaac Gym Preview 4 evidence;
- `rl_device`, `sim_device`, display type, and graphics device;
- whether vendor examples pass;
- whether joystick opened and observed axis indices/rest values;
- the first complete traceback and preflight JSON.

Never label a run verified if required Preview 4, CUDA, viewer, checkpoint, or
controller evidence is missing.
