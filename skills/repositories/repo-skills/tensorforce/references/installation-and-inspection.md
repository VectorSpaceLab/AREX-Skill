# Installation and Inspection

## When to read

Read this before installing Tensorforce, debugging imports, deciding optional extras, or checking whether a runtime can execute the bundled smoke scripts.

## Baseline package facts

- Distribution name: `Tensorforce`.
- Import package: `tensorforce`.
- Verified public root imports: `Agent`, `Environment`, `Runner`, `TensorforceError`.
- Version represented by this skill: `0.6.5`.
- Main runtime dependency family: TensorFlow 2.x plus Gym 0.21/0.22-era APIs, NumPy, h5py, matplotlib, msgpack, Pillow, and tqdm.
- The README says the project is no longer maintained; expect dependency drift on modern Python, TensorFlow, Gym/Gymnasium, and NumPy.

## Recommended runtime shape

Use an isolated Python environment. For old Tensorforce 0.6.x, Python 3.8 is the least surprising choice because the package metadata advertises Python 3.7/3.8 and old NumPy/Gym pins. Newer Python versions may work only after adjusting dependency pins.

A conservative CPU-first flow:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install tensorforce
python - <<'PY'
import tensorforce
from tensorforce import Agent, Environment, Runner
print(tensorforce.__version__)
PY
```

If installing from a local checkout, prefer a controlled environment and record the package/dependency versions that actually imported successfully.

## Known resolver issue

Tensorforce 0.6.5 metadata pins `numpy ~= 1.21.5` while `tensorflow == 2.12.1` requires a newer NumPy range. Modern pip can refuse to solve this combination. If this happens:

1. Do not treat a failed resolver as proof that Tensorforce APIs are unusable.
2. Choose a compatible Python/TensorFlow/NumPy set deliberately, then run import and smoke checks.
3. Document the deviation in the user's project notes; do not hide dependency overrides.
4. If reproducibility matters, use a constraints file for the exact working set and keep it with the experiment.

A working inspection environment for this skill used TensorFlow 2.12.1 with NumPy 1.23.x on Python 3.8, then verified import, custom environment execution, and Random/PPO agent construction. Users should still validate their own platform.

## Optional extras and when to install them

| Extra/surface | Install only when | Notes |
|---|---|---|
| `tfa` / TensorFlow Addons | A configuration explicitly needs TensorFlow Addons modules. | Match TFA to TensorFlow version. |
| `tune` | Running BOHB/Hyperband tuning workflows. | Requires HpBandSter/ConfigSpace and longer runs; not needed for ordinary `Runner`. |
| `gym`/Box2D/classic-control/Atari | Using Gym environments beyond the base package. | Tensorforce is Gym-era, not Gymnasium-first. |
| `ale`, `retro`, `vizdoom` | Running those simulator adapters. | Assets/ROMs/system packages may be separate from Python extras. |
| `carla` | Connecting to a CARLA simulator. | Requires external CARLA server/assets plus pygame/opencv. |
| `docs`/`tests` | Building docs or running repo-native tests. | Not needed for a user application runtime. |

## Smoke checks

Run the bundled root helper after installation:

```bash
python scripts/check_tensorforce_env.py --smoke-agent
```

Expected signals:

- package version prints;
- `Agent`, `Environment`, and `Runner` import;
- `Environment.create(environment='custom_cartpole')` can reset/execute once;
- optional `--smoke-agent` can create a cheap agent and act once.

If this fails, read [troubleshooting](troubleshooting.md) before changing random dependencies.
