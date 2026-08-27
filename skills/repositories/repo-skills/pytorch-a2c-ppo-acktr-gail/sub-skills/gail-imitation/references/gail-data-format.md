# GAIL expert data format

This repo expects GAIL expert demonstrations to be prepared outside the training loop. Upstream `gail_experts/README.md` says the expert HDF5 files are external data, should be placed in `gail_experts/`, then converted before training. Do not assume those files are bundled with the repo.

## HDF5 input contract

The original converter reads exactly these HDF5 datasets:

| Dataset | Expected shape | Meaning | Converted dtype |
| --- | --- | --- | --- |
| `obs_B_T_Do` | `[B, T, Do]` | Expert observations/states for `B` trajectories, time length `T`, observation dimension `Do`. | `torch.float32` |
| `a_B_T_Da` | `[B, T, Da]` | Expert actions aligned with observations; action dimension `Da`. | `torch.float32` |
| `r_B_T` | `[B, T]` | Expert rewards aligned by trajectory and timestep. Rewards are saved but not yielded by `ExpertDataset.__getitem__`. | `torch.float32` |
| `len_B` | `[B]` | Valid trajectory lengths before padding/subsampling. | `torch.int64` |

Validation rules to apply before training:

1. All four dataset names must exist exactly; renamed keys are not discovered automatically.
2. `obs_B_T_Do`, `a_B_T_Da`, and `r_B_T` must agree on `B` and `T`.
3. `len_B` must have length `B`; its values should be between `0` and `T`.
4. Observation dimension `Do` plus action dimension `Da` must match the discriminator input dimension used by `main.py`.

Use `../scripts/convert_gail_h5_to_pt.py` for a safe local conversion helper with these checks.

## PyTorch `.pt` output contract

The converter writes a dictionary accepted by `a2c_ppo_acktr.algo.gail.ExpertDataset`:

```python
{
    "states":  FloatTensor[B, T, Do],
    "actions": FloatTensor[B, T, Da],
    "rewards": FloatTensor[B, T],
    "lengths": LongTensor[B],
}
```

For a `HalfCheetah-v2` GAIL run, `main.py` derives the expert filename as `trajs_halfcheetah.pt` because it lowercases the part of `--env-name` before the first dash. If `--gail-experts-dir` is left at its default, that file is expected under `gail_experts/`.

## `ExpertDataset` behavior

`ExpertDataset(file_name, num_trajectories=4, subsample_frequency=20)` does the following:

- Loads the `.pt` dictionary with `torch.load(file_name)`.
- Randomly permutes available trajectories and keeps the first `num_trajectories` indices.
- Draws a random start offset in `[0, subsample_frequency)` for each selected trajectory.
- For non-`lengths` tensors, samples `data[i, start_idx[i]::subsample_frequency]` and stacks the sampled states/actions/rewards.
- Stores `lengths` as integer division by the subsample frequency.
- Builds a flat index map whose `__getitem__` returns only `(state, action)` pairs.

Operational implications:

- Set `torch.manual_seed(...)` before constructing `ExpertDataset` if deterministic subset selection matters for a diagnostic.
- The file should contain at least four usable trajectories for the default constructor.
- Very short trajectories can become length zero after integer division by `subsample_frequency`; reduce the frequency or provide longer demonstrations.
- Rewards are retained in the `.pt` file for provenance, but the discriminator update consumes expert state-action pairs.