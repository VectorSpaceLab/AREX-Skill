# GAIL troubleshooting

## `ModuleNotFoundError: No module named 'h5py'`

`setup.py` installs `gym`, `matplotlib`, `pybullet`, and `stable-baselines3`, but it does not declare `h5py`. The GAIL converter and `a2c_ppo_acktr.algo.gail` import `h5py`, so install dependencies from the repo requirements or add `h5py` explicitly in the active environment before conversion.

Safe probe:

```bash
python - <<'PY'
import h5py, torch
print('h5py', h5py.__version__)
print('torch', torch.__version__)
PY
```

## Expert file is missing

Symptoms include `FileNotFoundError` for a path like `gail_experts/trajs_halfcheetah.pt`.

Checklist:

1. Confirm the external HDF5 expert file was provided by the user or acquired outside the agent run.
2. Convert it to `.pt` with the bundled helper.
3. Match the name that `main.py` derives from `--env-name`: `HalfCheetah-v2` expects `trajs_halfcheetah.pt`.
4. If using a non-default location, pass `--gail-experts-dir`.

Do not silently download expert data. Ask the user for the file or explicit permission to fetch external data.

## Wrong HDF5 dataset names or shapes

The converter expects exact keys: `obs_B_T_Do`, `a_B_T_Da`, `r_B_T`, and `len_B`. Common failures:

- Datasets are renamed, nested under a group, or stored with flat names from another imitation-learning codebase.
- `obs_B_T_Do` and `a_B_T_Da` disagree on trajectory count `B` or timestep count `T`.
- `r_B_T` is stored as `[B, T, 1]` instead of `[B, T]`.
- `len_B` has shape `[B, 1]` instead of `[B]`.

Use a small inspection command before conversion:

```bash
python - <<'PY'
import h5py
with h5py.File('gail_experts/trajs_halfcheetah.h5', 'r') as f:
    for key in f.keys():
        print(key, f[key].shape, f[key].dtype)
PY
```

If the data is semantically equivalent but shaped differently, adapt it explicitly in a one-off preprocessing script rather than changing the documented `.pt` contract.

## `AssertionError` immediately after enabling `--gail`

`main.py` asserts that the observation space is one-dimensional when `--gail` is enabled. Atari and other image observations are not accepted by the built-in GAIL path. Route image-based training to `../training-workflows/` unless the user explicitly asks for a code change that adds image-observation GAIL support.

## State/action dimension mismatch

`Discriminator` receives concatenated state and action tensors, so the discriminator input dimension is `state_dim + action_dim`. If expert data dimensions do not match the environment policy rollouts, errors usually appear as tensor concatenation or linear-layer shape failures.

Checks:

- Compare `states.shape[-1]` in the `.pt` file with `envs.observation_space.shape[0]`.
- Compare `actions.shape[-1]` with `envs.action_space.shape[0]` for continuous-control `Box` action spaces.
- Ensure demonstrations came from the same environment version and action representation as the training environment.
- For discrete actions, this GAIL path is not a drop-in fit because `main.py` computes `envs.action_space.shape[0]`; route to model/action-space internals before modifying it.

## Empty or tiny `ExpertDataset`

`ExpertDataset` defaults to `num_trajectories=4` and `subsample_frequency=20`. Very short trajectories can become zero-length after integer division, and files with fewer trajectories than requested can trigger indexing issues.

Mitigations:

- Provide at least four sufficiently long trajectories.
- Lower `subsample_frequency` in code or in a diagnostic fork when expert sequences are short.
- Set `torch.manual_seed(...)` before construction when debugging random trajectory selection.

## Long training, simulator dependencies, and CUDA

The documented GAIL command is a long continuous-control training run. It may require MuJoCo or compatible Gym environments, can take a long time, and may optionally use CUDA unless `--no-cuda` is passed. These are not safe default verification steps.

Safe alternatives:

- Run converter `--help`.
- Convert a tiny synthetic HDF5 file.
- Optionally load the generated `.pt` with `ExpertDataset`.
- Build the intended `main.py --gail` command but do not execute it without explicit user approval.