# Install And Backends

This reference distills the DreamerV3 installation and operational backend evidence into commands and checks future agents can use without reopening the source repository.

## Baseline Runtime Facts

| Item | Contract |
| --- | --- |
| Python | 3.11+; the Docker recipe uses Python 3.11 because some optional suites are version-sensitive. |
| Distribution | `dreamer` version 3.3.1. |
| Import roots | `dreamerv3`, `embodied`, and optional `embodied.envs.<suite>` modules. |
| Base JAX requirement | `jax[cuda12]==0.4.33` plus CUDA 12 pip runtime packages from the dependency resolver. |
| Core dependencies | `elements`, `ninjax`, `optax`, `portal`, `scope`, `chex`, `einops`, `granular`, `jaxtyping`, `tqdm`, `numpy<2`, `ale_py`, `autorom[accept-rom-license]`, and related packages from the base requirements. |
| Default backend intent | DreamerV3 defaults to CUDA in config; CPU use is valid for debugging and inspection by selecting the CPU JAX platform. |

## Manual Setup Pattern

Use an isolated Python 3.11 environment. The exact environment manager is up to the host; the package can be installed from a release, wheel, sdist, or working copy that contains the DreamerV3 package.

```sh
python3.11 -m venv .venv-dreamer
. .venv-dreamer/bin/activate
python -m pip install --upgrade pip setuptools wheel

# If installing from a package root or checked-out release:
python -m pip install -e .

# If installing dependencies explicitly, keep the JAX/CUDA pin coherent:
python -m pip install 'jax[cuda12]==0.4.33' 'numpy<2' scope elements ninjax optax portal
python -m pip check
```

If CUDA is not available or the task is a small CPU smoke, run DreamerV3 with the CPU JAX platform selected. Training/config command construction belongs to `train-configure`; this sub-skill only records the backend consequence: CPU is a debugging/inspection backend, while serious image-control runs are expected to need accelerators.

## Base Import And Backend Smoke

Run this after installation or after repairing dependency conflicts:

```sh
python - <<'PY'
import dreamerv3, embodied
from embodied.envs import dummy
import jax, jax.numpy as jnp
print('jax_version', jax.__version__)
print('default_backend', jax.default_backend())
print('devices', [str(x) for x in jax.devices()])
print('tiny_sum', float(jnp.array([1.0, 2.0]).sum()))
env = dummy.Dummy({'image': (8, 8, 3)}, {'action': (2,)})
print('dummy_obs_space', sorted(env.obs_space.keys()))
print('dummy_act_space', sorted(env.act_space.keys()))
PY
```

Expected result:

- imports of `dreamerv3`, `embodied`, and the concrete dummy environment module succeed;
- JAX reports either `cpu` or `gpu` as the default backend and evaluates a tiny array;
- dummy environment spaces can be constructed.

Important import detail: import concrete environment modules directly when checking them, for example `from embodied.envs import dummy`; do not assume importing only `embodied` attaches every submodule as an attribute.

## CUDA Setup Checks

DreamerV3's base dependency pin is for JAX 0.4.33 with CUDA 12 packages. For CUDA issues, confirm versions before changing model or training flags:

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

If JAX falls back to CPU unexpectedly, check that:

1. the NVIDIA driver supports the CUDA runtime pulled by the JAX CUDA wheel;
2. `jax` and `jaxlib` versions match;
3. the environment did not install both incompatible CPU and CUDA JAX variants;
4. no host variable hides GPUs from the process.

Out-of-memory errors are often reported after an earlier failure. Scroll to the first CUDA/JAX error in the log. To separate version mismatch from capacity, run the tiny JAX smoke above, then try a deliberately small DreamerV3 debug run through `train-configure`.

## Docker Evidence And Caveats

The bundled Docker recipe is an operational reference, not something this skill runs automatically. It uses:

- an NVIDIA-driver Ubuntu 24.04 base image;
- Python 3.11 virtual environment;
- system packages including `ffmpeg`, `git`, `curl`, `libglew-dev`, `x11-xserver-utils`, `xvfb`, and `wget`;
- optional environment-suite installers for DMLab, Atari/AutoROM, ProcGen, Crafter, DeepMind Control, Memory Maze, and MineRL;
- `MUJOCO_GL=egl` for MuJoCo rendering;
- OpenJDK 8 for MineRL;
- a final requirements install that applies the repo's pinned dependencies.

The entrypoint prints a small package/GPU diagnostic, attempts to read GCP metadata, prints `nvidia-smi`, and wraps the user command in `xvfb-run` with a 1024x768x24 virtual display. When adapting it outside GCP, add short `curl` timeouts for metadata probes to avoid slow startup on networks that blackhole metadata addresses.

Docker run pattern:

```sh
docker build -t dreamerv3-runtime .
docker run --rm -it --gpus all -v "$HOME/logdir/dreamer:/logdir" dreamerv3-runtime \
  python -m dreamerv3.main --logdir /logdir/run --configs <config> --task <suite_task>
```

Keep host-side logdirs mounted so JSONL, Scope summaries, checkpoints, and replay data survive container removal.

## Optional Environment Suite Dependency Map

Use [../scripts/check_optional_env_imports.py](../scripts/check_optional_env_imports.py) to check availability before constructing expensive environments.

| Suite/task prefix | DreamerV3 module | Python packages/modules to check | System/runtime notes | Required only when |
| --- | --- | --- | --- | --- |
| `dummy` | `embodied.envs.dummy` | base package only | No optional suite dependency. | Debug/import/smoke tasks. |
| `atari`, `atari100k` | `embodied.envs.atari` | `ale_py`, `ale_py.roms`, `autorom`; optional `cv2` if resize is `opencv`; `PIL` for default resize. | ROMs come from AutoROM or `ALE_ROM_PATH`. Use accepted ROM license. | Atari tasks. |
| `crafter` | `embodied.envs.crafter` | `crafter` | Optional per-env stats can write `stats.jsonl` when achievement logging is enabled. | Crafter reward/noreward tasks. |
| `dmc` | `embodied.envs.dmc` | `dm_control` | Set or inherit `MUJOCO_GL=egl` for headless EGL rendering; needs GL/EGL libraries. | DeepMind Control tasks. |
| `loconav` | `embodied.envs.loconav` and `loconav_quadruped` | `dm_control` | Also uses MuJoCo/composer locomotion modules and EGL rendering. | Locomotion navigation tasks. |
| `dmlab` | `embodied.envs.dmlab` | `deepmind_lab` | Native DMLab install is system-sensitive; Docker installs it via an external installer. NumPy compatibility matters. | DMLab30 tasks. |
| `minecraft` | `embodied.envs.minecraft`, `minecraft_flat` | `minerl` | Needs Java; Docker uses OpenJDK 8 and a Linux CPython 3.11 MineRL mirror wheel. NumPy aliases may require patched/compatible packages. | Minecraft wood/climb/diamond tasks. |
| `procgen` | `embodied.envs.procgen` | `procgen` or `procgen_mirror`, `gym`, `PIL`; optional `cv2` for OpenCV resize. | Gym registration names can differ; the wrapper tries both `procgen:procgen-<task>-v0` and `procgen-<task>-v0`. | ProcGen tasks. |
| `gym` | `embodied.envs.from_gym` | `gym` | Underlies generic Gym tasks and some wrappers. | Gym-style tasks. |
| `memmaze` | `dreamerv3.main` plus `from_gym` | `memory_maze`, `gym` | Uses Gym id `MemoryMaze-<task>-v0`. | Memory Maze tasks. |
| `bsuite` | `embodied.envs.bsuite` | `bsuite` | BSuite result logging is stateful; interrupted runs cannot be reliably restarted. | BSuite tasks. |

Optional suite failure should not block an unrelated suite. Example: a missing `deepmind_lab` package is a blocker for `dmlab_*`, but not for `atari_*`, `dummy_*`, or pre-existing result summarization.

## Setup Validation Decision Tree

1. **Import roots fail**: repair the base DreamerV3 install before checking optional suites.
2. **JAX CPU smoke fails**: fix JAX/JAXLIB dependency mismatch or Python version first.
3. **JAX CPU works but CUDA fails**: inspect driver, wheel variant, `nvidia-smi`, and first CUDA error; do not treat CPU success as proof of CUDA training readiness.
4. **Optional suite import missing**: determine the selected `--task` suite prefix; install only that suite's dependencies.
5. **Viewer or plotting fails**: preserve training logs and switch to JSONL summarization while repairing optional viewer/plot dependencies.
