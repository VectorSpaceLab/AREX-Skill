# MJX and JAX API reference

This reference describes the public import paths and the observed input/output
contracts. Importing the optional module requires the MJX dependency tier.

## Environment factory and registry

```python
from myosuite.envs.myo import mjx

env = mjx.make(name, config_overrides=None)
```

`name` is a string. `config_overrides` is an optional mapping consumed by the
MuJoCo Playground-style configuration; keep overrides JSON/config-dict-like
and use small `num_envs` values for smoke tests. The result is an MJX
environment object with:

- `reset(rng: jax.Array) -> State`;
- `step(state: State, action: jax.Array) -> State`;
- `action_size -> int`;
- `mj_model -> mujoco.MjModel`;
- `mjx_model -> mujoco.mjx.Model`;
- `xml_path -> str`.

`State` is a functional record. Its relevant fields are `data`, `obs`,
`reward`, `done`, `metrics`, and `info`. `obs` is a dictionary; the built-in
pose and reach environments use the `state` key. `info` contains a JAX RNG,
`step_count`, and either target angles or target site positions. The action
must have the last dimension equal to `action_size`; use a JAX array and match
the model's floating-point dtype.

The factory registers these base names when requested:

- `MjxElbowPoseFixed-v0`
- `MjxElbowPoseRandom-v0`
- `MjxFingerPoseFixed-v0`
- `MjxFingerPoseRandom-v0`
- `MjxHandReachFixed-v0`
- `MjxHandReachRandom-v0`

`myosuite.envs.myo.mjx.myo_registry` exposes `register_environment`,
`register_environment_with_variants`, `load`, `get_default_config`,
`get_base_env_name`, and `ALL_ENVS`. The registry is process-local. The
factory's registration is lazy, so call `make` before relying on a name being
available. Fatigue variants are registered with the `MjxFati` prefix when a
base variant is registered.

## Lower-level model/data construction

The implementation class is
`myosuite.envs.myo.mjx.mjx_base_env.MjxMyoBase`. Its useful properties are
`mj_model`, `mjx_model`, `action_size`, and `xml_path`. The helper
`make_data(model, qpos=None, qvel=None, ctrl=None, act=None,
mocap_pos=None, mocap_quat=None, impl=None, naconmax=None, njmax=None,
naccdmax=None, device=None)` returns `mujoco.mjx.Data` with the supplied fields
replaced. Shapes must match the MuJoCo model; mocap fields are reshaped to the
model's mocap dimensions.

`MjxMyoBase.norm_actions(action)` applies
`1 / (1 + exp(-5 * (action - 0.5)))`. The base configuration enables this
normalization. The fatigue wrapper disables base normalization and applies its
own normalization before fatigue processing. Do not normalize an action twice.

The pose environment (`MjxPoseEnvV0`) samples joint targets from configured
ranges and returns a `state` observation containing qpos, scaled qvel, act, and
pose error. The reach environment (`MjxReachEnvV0`) samples target site
positions and returns qpos, scaled qvel, act, tip positions, and flattened
reach error. Rewards and termination are environment-specific; inspect the
configuration rather than assuming the CPU environment's reward schema.

## Fatigue JAX helpers

```python
from myosuite.envs.myo.mjx.fatigue_jax import CumulativeFatigue

fatigue = CumulativeFatigue(mj_model, frame_skip=1)
state = fatigue.reset(
    rng=jax.random.PRNGKey(0),
    fatigue_reset_vec=None,
    fatigue_reset_random=False,
)
state = fatigue.compute_act(target_load, fatigue_state=state)
effort = fatigue.get_effort(target_load, fatigue_state=state)
```

`target_load` is a vector for the muscle actuators, and `state` is a mapping
with equal-length vectors `MA` (active), `MR` (resting), and `MF` (fatigued).
The default reset is MA=0, MR=1, MF=0. A reset vector supplies MF and derives
MR=1-MF with MA=0; its length must equal the number of muscle actuators. A
random reset consumes the supplied PRNG key and keeps the three state vectors
summing to one. `compute_act` returns a new mapping and clips transfer rates to
preserve the state bounds. `get_effort` returns a scalar norm.

Parameter mutators are `set_FatigueCoefficient(F)`,
`set_RecoveryCoefficient(R)`, and `set_RecoveryMultiplier(r)`. They update JAX
scalar parameters and affect subsequent calls. Use `jax.jit`/`jax.vmap` around
pure calls only after confirming that model-derived static values are fixed.

`FatigueWrapper` wraps an MJX environment. Its configuration keys are
`fatigue_reset_vec`, `fatigue_reset_random`, and `fatigue_obs_keys`; allowed
observation keys are exactly `MA`, `MR`, and `MF`. It allocates three `nu`
blocks in model `userdata`, stores fatigue state there, replaces muscle actions
with active muscle-unit values, and optionally appends selected fatigue blocks
to the `state` observation. A wrapper changes observation dimensions and action
semantics; record that change in an experiment contract.

## Quaternion and vector math

The JAX module is `myosuite.utils.quat_math_jax`. It provides:

- `mulQuat(qa, qb)` and `negQuat(quat)`;
- `quat2Vel(quat, dt=1)` and `quatDiff2Vel(quat1, quat2, dt)`;
- `diffQuat(quat1, quat2)` and `axis_angle2quat(axis, angle)`;
- `euler2mat`, `euler2quat`, `mat2euler`, `mat2quat`;
- `quat2mat`, `quat2euler`, `quat2euler_intrinsic`,
  `intrinsic_euler2quat`;
- `rotVecMatT`, `rotVecMat`, and `rotVecQuat`.

The convention is scalar-first `[w, x, y, z]`. JAX conversion helpers cast
Euler/matrix/quaternion inputs to float32 and return JAX arrays. Inputs are
normally shape `(3,)`, `(4,)`, or `(3, 3)`; several conversion helpers also
support leading batch dimensions. `quat2mat` returns identity for a near-zero
quaternion norm. `quat2Vel` adds a small denominator stabilizer for a near-zero
axis, so a zero rotation's axis is not a meaningful physical direction.

For parity, compare the resulting rotation matrices rather than raw
quaternions when either output may differ by global sign (`q` and `-q` encode
the same rotation). Compare scalar/vector functions with a documented
`tolerance`, and compare JAX results after conversion with `numpy.asarray`.
The NumPy implementation uses float64-oriented intermediates while the JAX
implementation explicitly uses float32, so exact equality is not a valid
cross-backend contract.

## JAX reference motion

```python
from myosuite.logger.reference_motion_jax import (
    ReferenceMotion, ReferenceType, ReferenceStruct,
)

reference = ReferenceMotion(data_or_filename, motion_extrapolation=False)
robot_init, object_init = reference.get_init()
frame = reference.get_reference(time)
indices = reference.find_timeslot_in_reference(time)
reference.reset()
```

The input is a dict or an `.npz`/pickle filename. The data dict must contain
`time`; optional `robot`, `robot_vel`, `object`, `robot_init`, and `object_init`
fields are resolved according to the reference type. Robot/object trajectories
are two-dimensional `(frames, joints)` arrays and init vectors are one-
dimensional. One frame is `FIXED`, two rows are `RANDOM` bounds, and more than
two rows are `TRACK`. Missing fixed/track init values use the first frame;
missing random init values use the implementation's default bound-derived
initialization.

`get_reference` returns a `ReferenceStruct` with `time`, `robot`,
`robot_vel`, `object`, `robot_init`, and `object_init`. Track references use
exact frames or interpolation and can hold the final frame when
`motion_extrapolation=True`. The observed JAX implementation creates a fixed
PRNG key internally for random references, so do not promise externally seeded
random draws without checking the installed version. Keep any parity issue
between JAX and NumPy explicit; see [troubleshooting.md](troubleshooting.md).
