# Data Formats

## Offline Transition Data

Offline replay filling expects transition-style fields:

| Field | Meaning | Shape notes |
| --- | --- | --- |
| `observations` / `obs` | State at time `t` | Must match environment observation space. |
| `actions` | Action at time `t` | Must match action space dtype/shape. |
| `rewards` | Scalar reward | Usually one reward per transition. |
| `next_observations` / derived next row | State at time `t+1` | Some examples derive it from `observations[i + 1]`. |
| `terminals` / `dones` | Episode end flag | Convert to bool where needed. |

AgileRL examples wrap each row in `Transition`, add a vectorized dimension with `unsqueeze(0)`, set `batch_size = [1]`, and call `to_tensordict()` before adding to replay.

## HDF5

For HDF5 datasets, check keys and lengths before training:

```python
with h5py.File(path, "r") as dataset:
    print(dataset.keys())
    print(dataset["observations"].shape, dataset["actions"].shape, dataset["rewards"].shape)
```

Do not assume every HDF5 file uses the same key names.

## Minari

Minari can manage offline RL datasets and may fetch remote data. For agent workflows, record whether the dataset is already local before running code that downloads.

## Contextual Bandits

Bandit data usually has:

- `features`: rows of context values.
- `targets`: labels/reward arms.

`BanditEnv(features, targets)` derives `context_dim` and `arms`. Validate missing values, target encoding, and feature min/max before creating spaces.
