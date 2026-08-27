# Controller workflow and policy boundary

This reference explains the source's order and contracts without providing a
launcher. Every step that can move a robot or change a host is marked
**UNSAFE / HUMAN-APPROVED ONLY**. For physical gates, read
[safety.md](safety.md) first.

## Preparation and routing

1. Select a policy directory produced by the training workflow. A deployment
   label is relative to the run store; the source example resolves a label like
   `gait-conditioned-agility/pretrain-v0/train`, then chooses a run directory
   containing `parameters.pkl` and a `checkpoints/` directory.
2. Route the policy/checkpoint and observation-history contract to
   `training-and-policy`. Route actuator-network fitting, deployment-log
   extraction, or motor-model changes to `actuator-network`. Do not patch a
   deployment script to compensate for an unverified training shape.
3. Use `validate_policy_artifacts.py` to check presence, sizes, and an optional
   JSON configuration. It intentionally does not unpickle `parameters.pkl`,
   load TorchScript, import the SDK, run inference, or publish an action.
4. Confirm the target is a Go1 Edu and record the intended CPU/Jetson
   architecture, LCM URL, network interface, image provenance, and rollback
   checkpoint. Missing hardware is `BLOCKED_REQUIRED_BACKEND`.

## Transfer → SDK → controller order

The source evidence establishes this order, but the generated skill does not
execute it:

1. **Transfer (UNSAFE):** an approved operator copies only the reviewed
   deployment package, setup metadata, and selected run/checkpoint artifacts to
   the robot host using the organization's SSH/rsync process. Do not copy
   private credentials, unrelated runs, or the whole source checkout.
2. **SDK bridge (UNSAFE):** on the target, the Unitree SDK-side LCM bridge
   (`lcm_position`) is started first. It must be compiled for the target
   architecture and verified against the same message contract. An ARM binary
   on x86 is a known failure; see [troubleshooting](troubleshooting.md).
3. **Controller container (UNSAFE):** the deployment container is started only
   after the bridge, host networking, device/runtime, and safety approvals are
   confirmed. The controller's Python setup and `deploy_policy.py` then create
   the state estimator, RC profile, LCM agent, history wrapper, policy, and
   runner in that order.
4. **Physical gates (UNSAFE):** place the robot in damping mode, suspend it,
   approve calibration R2 #1, inspect the nominal pose, then approve R2 #2.
   Only then may a human operator permit the loop. This skill never sends the
   R2 event or target message.

If transfer, SDK, container, calibration, or controller startup is discussed,
repeat that it is a human-approved unsafe action. Do not turn this sequence into
a bundled launcher.

## Policy and checkpoint contract

The source `deploy_policy.py` expects a run directory with:

- `parameters.pkl`, containing the saved `Cfg` payload used to reconstruct the
  deployment configuration. Pickle is executable serialization; the bundled
  validator checks its presence/signature only and does not deserialize it.
- `checkpoints/body_latest.jit`, the TorchScript body policy.
- `checkpoints/adaptation_module_latest.jit`, the TorchScript adaptation module.

At each control step the deployment policy receives an `obs_history` tensor and
computes the latent with the adaptation module, then concatenates history and
latent for the body module. The policy returns at least twelve action values.
The exact observation width, history length, action clipping, command count,
normalization scales, PD gains, `control.action_scale`,
`control.hip_scale_reduction`, `control.decimation`, and `sim.dt` come from the
saved configuration. Validate these against the training export; do not guess
or run a mismatched checkpoint. The `training-and-policy` skill owns the
checkpoint semantics and policy evaluation.

## Twelve-joint mapping

The configuration's nominal/default order in `LCMAgent` is:

| policy/default index | joint |
|---:|---|
| 0–2 | FL hip, thigh, calf |
| 3–5 | FR hip, thigh, calf |
| 6–8 | RL hip, thigh, calf |
| 9–11 | RR hip, thigh, calf |

The deployment source uses this explicit permutation for both state estimates
and outgoing targets:

```text
[3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8]
```

Before applying the permutation to outgoing targets, it multiplies indices
`[0, 3, 6, 9]` (the four hip entries in policy/default order) by
`control.hip_scale_reduction`, multiplies actions by `control.action_scale`,
and adds `default_dof_pos`. It then sends the reordered twelve-element target
array. The state estimator applies the same source permutation to `q`, `qd`,
and `tau_est`; contact state uses `[1, 0, 3, 2]`. Preserve this mapping exactly
and do not infer a different SDK ordering from a diagram.

## Timing and observation update

`deploy_policy.py` constructs its RC profile with `control_dt = 0.02`; this is
50 Hz. `LCMAgent.dt` is `control.decimation * sim.dt`, so the saved policy
configuration must produce the same effective period. `LCMAgent.step()` publishes
one target, sleeps for the remaining period, refreshes state, advances gait
clock inputs, and returns the next observation. The history wrapper shifts the
observation history by one observation per step and resets it to zeros at reset.
Timing drift, stale LCM state, or a mismatched history width is a stop condition.

## RC command indexes, modes, and gait profiles

The source command vector uses these indexes before truncation to
`num_commands`:

| index | meaning |
|---:|---|
| 0 | forward/longitudinal velocity |
| 1 | lateral velocity |
| 2 | yaw velocity |
| 3 | body-height command |
| 4 | step frequency |
| 5 | phase |
| 6 | offset |
| 7 | bound |
| 8 | duration |
| 9 | foot-swing height |
| 10 | body pitch |
| 11 | body roll |
| 12 | stance width |
| 13 | stance length |
| 14–18 | auxiliary/reserved zeros in the estimator output |

The deployment script uses RC x/y/yaw scales of `3.5`, `0.6`, and `5.0` in its
example. These are policy-specific limits, not universal safe operating limits.
The source maps forward velocity from the left-stick vertical value and yaw
from the negative right-stick horizontal value. The left upper switch cycles
left-stick modes: body height, lateral velocity, stance width. The right upper
switch cycles right-stick modes: step frequency, foot-swing height, body pitch.
Frequency is mapped between 2 and 4; foot-swing height is bounded by the source
formula; body pitch is scaled by `-0.4`.

`rc_command_lcmt.mode` selects the gait pattern:

- mode `0`: source default trotting pattern (`phase=0.5`, `offset=0`,
  `bound=0`, `duration=0.5`);
- modes `1`, `2`, and `3`: source-defined alternatives with respectively
  `(phase, offset, bound)` of `(0,0,0)`, `(0,0.5,0)`, and `(0,0,0.5)`, each with
  duration `0.5`.

The source does not name modes 1–3 in this module; preserve the numeric contract
rather than inventing gait names. `command_profile.py` also contains timed
constant-acceleration, elegant forward, yaw, and JSON gait profiles. Triggered
profiles are button-indexed 0–3 and are reset on a button edge. Review their
units and total duration before any operator uses one.

## Calibration, emergency, and logging behavior

`DeploymentRunner.run()` requires a control agent, policy, and command profile,
then calibrates before the loop. It logs observation, reward/done fields,
timestep/time, action, RPY, torques, and policy information through
`MultiLogger`; log directories are timestamped under the configured experiment
root and are serialized as pickle. Button-driven probing/logging can reset the
logger, calibrate, save, and resume. Treat logs as potentially sensitive and
untrusted generated state; route analysis to `actuator-network` and never
replace a missing safety gate with a logger action.

A tilt beyond 1.6 radians in roll or pitch invokes the source's low-pose
calibration attempt. An operator must instead follow the emergency stop policy
in [safety.md](safety.md), inspect the robot, and require fresh approval before
any recovery. Keyboard interrupts save a log in the source, but a saved log is
not evidence that the robot stopped safely.
