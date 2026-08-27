# Troubleshooting

Use this guide for DreamerV3 install/import/backend/viewer/plotting/optional-suite failures. Fix the earliest concrete error first; later stack frames often report symptoms rather than causes.

## Fast Triage

| Symptom | First check | Likely scope |
| --- | --- | --- |
| `ModuleNotFoundError: dreamerv3` or `embodied` | `python -m pip show dreamer` and `python -m pip check` | Base install broken; blocks all package use. |
| JAX imports but sees CPU only | JAX/JAXLIB versions, CUDA wheel variant, `nvidia-smi`, GPU visibility | Blocks CUDA training claims, not CPU/debug/result reading. |
| Optional suite import fails | Suite prefix in `--task`; run optional import checker | Blocks only that suite. |
| Scope viewer fails | `python -m scope.viewer --help`, port availability, basedir | Viewer issue; JSONL summaries can continue. |
| `episode/score` missing | Has any episode finished? Is `scores.jsonl` present? | May be normal early in a run. |
| Plot script fails on pandas/matplotlib/layout | Use lightweight summarizer first | Plot dependency/layout issue, not necessarily run failure. |
| Resume fails with PyTree/checkpoint mismatch | Compare logdir/config/model size | Incompatible checkpoint; use matching config or fresh logdir. |

## Base Install And Import Failures

### `ModuleNotFoundError` for core imports

Run:

```sh
python - <<'PY'
import sys
print(sys.version)
import dreamerv3, embodied
print('ok')
PY
python -m pip check
```

Fixes:

- Use Python 3.11+.
- Reinstall the `dreamer` package and its requirements in the active environment.
- Avoid mixing packages from multiple environments.
- Import concrete submodules directly for checks, for example `from embodied.envs import dummy`; importing `embodied` alone does not prove every submodule is attached.

### NumPy compatibility

The base requirement is `numpy<2`. Some optional suites are stricter:

- DMLab is sensitive to NumPy 2+.
- older MineRL stacks may require NumPy aliases or versions below 1.24 unless patched.

If an optional suite fails with `np.float`, `np.int`, or ABI errors, install a suite-compatible NumPy version in that environment rather than changing DreamerV3 logic.

## JAX And CUDA Failures

Run:

```sh
python - <<'PY'
import jax, jaxlib
print('jax', jax.__version__)
print('jaxlib', jaxlib.__version__)
print('backend', jax.default_backend())
print('devices', jax.devices())
PY
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
python -m pip check
```

Common causes:

- `jax` and `jaxlib` versions do not match.
- CPU-only JAX package shadowed the CUDA build.
- NVIDIA driver is too old for the CUDA runtime expected by the JAX wheel.
- GPU visibility is disabled by host/container variables.
- CUDA out-of-memory happened before the final stack trace.

Actions:

1. Confirm tiny JAX array evaluation works on the intended backend.
2. If backend is CPU but GPU is required, repair the JAX CUDA install before tuning DreamerV3.
3. If backend is GPU but training OOMs, try the smallest debug configuration through `train-configure` to separate capacity from dependency failure.
4. Do not treat CPU success as proof that production CUDA training is verified.

## Atari And AutoROM

Symptoms:

- `ModuleNotFoundError: ale_py`
- missing ROM errors
- unknown Atari game name
- image resize errors involving OpenCV or Pillow

Checks:

```sh
python scripts/check_optional_env_imports.py
python - <<'PY'
import importlib.util
print('ale_py', importlib.util.find_spec('ale_py') is not None)
print('autorom', importlib.util.find_spec('AutoROM') is not None or importlib.util.find_spec('autorom') is not None)
PY
```

Fixes:

- Install `ale_py==0.9.0` and `autorom[accept-rom-license]==0.6.1` or a compatible Atari stack.
- Run AutoROM with license acceptance where policy permits.
- If using private ROMs, set `ALE_ROM_PATH` to a directory containing `<game>.bin` files.
- Default resize uses Pillow; install OpenCV only if selecting `resize=opencv`.

## DeepMind Control, MuJoCo, And Loconav

Symptoms:

- `ModuleNotFoundError: dm_control`
- MuJoCo cannot create an EGL/OpenGL context
- render failures on headless machines

Fixes:

```sh
export MUJOCO_GL=egl
python scripts/check_optional_env_imports.py
```

- Install `dm_control` and required GL/EGL system libraries.
- On headless hosts, prefer EGL or wrap with `xvfb-run` if an X11 context is required.
- Loconav uses DeepMind Control composer/locomotion modules, so a minimal `dm_control` import may not prove all locomotion extras work.

## DMLab

Symptoms:

- `ModuleNotFoundError: deepmind_lab`
- native library load errors
- DMLab levels not found
- NumPy ABI errors

Fixes:

- Use a DMLab-compatible Python/NumPy combination.
- Install native/system dependencies as documented by the DMLab package or a known-good container recipe.
- Treat DMLab as optional unless the selected task prefix is `dmlab`.
- For language DMLab tasks, remember that observations may include an instruction embedding in addition to images.

## Minecraft / MineRL

Symptoms:

- `ModuleNotFoundError: minerl`
- Java not found or wrong Java version
- MineRL wheel not available for platform/Python
- NumPy alias failures

Fixes:

- Install a MineRL build compatible with Python 3.11 and the host platform.
- Provide Java; the reference Docker recipe uses OpenJDK 8.
- Keep NumPy compatible with the selected MineRL build.
- Treat Minecraft tasks (`minecraft_wood`, `minecraft_climb`, `minecraft_diamond`) as optional-suite tasks; missing MineRL does not block other suites.

## ProcGen And Gym

Symptoms:

- `ModuleNotFoundError: procgen` or `gym`
- Gym environment id registration fails
- resize errors

Fixes:

- Install `procgen` or `procgen_mirror` plus `gym`.
- The wrapper tries both `procgen:procgen-<task>-v0` and `procgen-<task>-v0`; a registration failure after both attempts usually means the package is missing or incompatible.
- Default resize uses Pillow. Install OpenCV only if selecting OpenCV resize.

## Crafter

Symptoms:

- `ModuleNotFoundError: crafter`
- achievement stats absent

Fixes:

- Install `crafter` only for Crafter tasks.
- Achievement stats are environment-side optional logs; absence of `stats.jsonl` is expected unless environment logging is enabled.
- Continue using DreamerV3 `metrics.jsonl` and `scores.jsonl` as the portable run outputs.

## Scope Viewer

Symptoms:

- `No module named scope`
- browser cannot connect
- no runs visible
- port already in use

Fixes:

```sh
python -m pip install -U scope
python -m scope.viewer --basedir <logdir-parent> --port 8000
```

- Point `--basedir` at the parent containing run directories.
- Use a different port if 8000 is busy.
- On remote hosts, use SSH port forwarding or inspect JSONL directly.
- Viewer failure does not invalidate metrics if JSONL files are healthy.

## JSONL And Plotting Failures

### Missing key

```sh
python scripts/metrics_summary.py --input <logdir> --list-keys
```

Then rerun with an actual key. Common candidates include `episode/score`, `episode/length`, `fps/policy`, `fps/train`, `replay/inserts`, and `train/loss/...`.

### Malformed JSONL line

A crash can truncate the final line. Robust readers should skip malformed lines and report the count. Do not delete the whole file unless you have a backup.

### Plot dependency failure

The full plotting workflow needs pandas, NumPy, Matplotlib, ruamel.yaml, tqdm, and elements plus an expected run directory layout. For quick inspection, use:

```sh
python scripts/metrics_summary.py --input <path> --key episode/score --last 20
```

### Gzip score artifact confusion

Gzipped benchmark score files are JSON arrays of records with `task`, `method`, `seed`, `xs`, and `ys`. Use `episode/score`, `score`, or `ys` as the summary key. Do not parse them as JSONL.

## Docker And Entrypoint Issues

| Symptom | Fix |
| --- | --- |
| Container sees no GPU | Run with GPU runtime support such as `--gpus all`; confirm host `nvidia-smi`. |
| `xvfb-run` missing | Install `xvfb` and X11 utility packages or remove the wrapper only for suites that never render through X11. |
| GCP metadata probe is slow/noisy | Add short `curl` timeouts or skip metadata reporting outside GCP. |
| Logs disappear after container exit | Mount a host logdir volume and write logs under that mount. |
| MuJoCo render fails in container | Keep `MUJOCO_GL=egl`, install GL/EGL libraries, and verify GPU passthrough. |

## Resume And Logdir Errors

- Reusing a logdir resumes; it is not a fresh run.
- A `Too many leaves for PyTreeDef` or similar checkpoint tree error usually means the logdir contains a checkpoint from a different config/model structure.
- Use a fresh logdir for changed model size/configs, or restore the exact matching config before resume.
- Preserve partial logs after failure. They help identify whether the run reached logging, checkpoints, or scores before crashing.
