# Actuator log and sample format

Read this before using [`inspect_actuator_log.py`](../scripts/inspect_actuator_log.py)
or [`prepare_actuator_data.py`](../scripts/prepare_actuator_data.py). The source
workflow is `scripts/actuator_net/utils.py`; deployment logging behavior comes
from `go1_gym_deploy/utils/logger.py`.

## Deployment-log envelope

`MultiLogger.save()` serializes a dictionary with one entry per robot. The
relevant entry is normally:

```text
{
  "hardware_closed_loop": [config_dict, infos]
}
```

`infos` is a chronological list of dictionaries. Each call to
`EpisodeLogger.log(info)` copies the record and converts Torch tensors to CPU
NumPy arrays; image fields can also be present but are irrelevant to actuator
fitting. The supplied example log uses the second element of
`hardware_closed_loop` and contains 3,371 records. Use a trusted pickle only:
Python pickle deserialization is not safe for untrusted input.

For portable tests, the bundled scripts also accept JSON in either of these
forms:

```json
{"records": [{"joint_pos": [...], "joint_pos_target": [...],
               "joint_vel": [...], "tau_est": [...], "torques": [...]}]}
```

or the same `{"hardware_closed_loop": [config, records]}` envelope. A JSON
list of records is accepted as a convenience. The JSON fixture must contain
numbers, not paths to another file.

## Required record fields and shapes

Every record used for fitting must contain these five keys:

| key | normalized shape | role |
| --- | --- | --- |
| `joint_pos` | 12 values; source commonly stores `(1, 12)` | measured joint position |
| `joint_pos_target` | 12 values; source commonly stores `(1, 12)` | commanded/target joint position |
| `joint_vel` | 12 values; source commonly stores `(1, 12)` | measured joint velocity |
| `tau_est` | 12 values, commonly `(12,)` | **one target torque value per joint** |
| `torques` | 12 values, commonly `(12,)` | logged/reference torque; retained for diagnostics, not the fitting target |

The example log was inspected with NumPy arrays shaped `(1, 12)` for the first
three fields and `(12,)` for `tau_est` and `torques`. The validator flattens
only singleton/nested array wrappers and then requires exactly 12 finite
numeric values. It does not silently pad, truncate, reorder, normalize, or
broadcast joints.

The 12 joints are treated as exchangeable for this model: a single network is
trained from all per-joint samples. Joint ordering is the ordering already in
the log; this skill does not infer a new robot joint map. Robot collection,
LCM state/action channels, and physical safety are owned by
[`robot-deployment`](../../robot-deployment/SKILL.md).

## Six inputs and one target

For each joint `j` and aligned time index `t`, define:

```text
error[t, j] = joint_pos[t, j] - joint_pos_target[t, j]

x[t, j] = [
    error[t,     j], error[t - 1, j], error[t - 2, j],
    joint_vel[t,     j], joint_vel[t - 1, j], joint_vel[t - 2, j],
]
y[t, j] = [tau_est[t, j]]
```

Thus the six features are three shifted position errors followed by three
shifted velocities. The target is one `tau_est` value for the same joint and
current time. `torques` is not substituted for a missing `tau_est`.

The source uses `step = 2` and slices that align targets at `t = 2 ... T-2`
(inclusive) with the three rows at `t`, `t-1`, and `t-2`. For `T` input records
this produces `T - 3` samples per joint and `12 * (T - 3)` rows total. The
prepared JSON preserves source-compatible joint-block order: all times for
joint 0, then all times for joint 1, through joint 11.

The minimum usable history is **four complete records** (`T >= 4`), yielding
one sample per joint. Fewer records are an error, not a reason to duplicate
history. Missing, malformed, non-finite, or inconsistent records are rejected
with a non-zero exit by the bundled scripts.

## Split and reproducibility

The source `train_actuator_network` computes:

```text
num_train = num_samples // 5 * 4
num_test  = num_samples - num_train
```

This is a four/five (80%/20%) split, implemented with PyTorch
`random_split`; it is not a chronological holdout and has no seed in the
source function. A data-preparation run is deterministic, but training split
membership and parameter initialization are not reproducible unless the caller
sets explicit PyTorch/loader seeds in an adapted training harness. Do not use
the split to claim time-series generalization.

See [workflow.md](workflow.md) for the safe evaluation/training boundary and
[api-reference.md](api-reference.md) for the exact source signatures.
