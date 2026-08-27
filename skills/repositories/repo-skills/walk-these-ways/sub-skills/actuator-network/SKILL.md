---
name: actuator-network
description: "Validate Go1 deployment logs, build six-feature per-joint actuator
  samples, evaluate the small actuator MLP on CPU, and optionally train and
  export a bounded TorchScript model with safe diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Actuator Network

Use this sub-skill for the offline actuator-model workflow: inspect a
`hardware_closed_loop` deployment log, turn its 12-joint state history into
six-feature samples, evaluate the supplied TorchScript actuator model on CPU,
or deliberately opt in to a bounded CUDA training/export run.

## Route and safety boundary

1. Read [data format](references/data-format.md) before interpreting a log or
   constructing samples.
2. Use [workflow](references/workflow.md) to choose CPU evaluation, data-only
   extraction, or explicitly approved training/export.
3. Consult [API reference](references/api-reference.md) for the source helper
   signatures and [troubleshooting](references/troubleshooting.md) for
   incomplete logs, shape errors, paths, CUDA, and headless operation.
4. Run [`inspect_actuator_log.py`](scripts/inspect_actuator_log.py) first. It is
   read-only and validates a pickle log or portable JSON fixture without
   importing Torch, training, networking, or plotting.
5. Run [`prepare_actuator_data.py`](scripts/prepare_actuator_data.py) to emit a
   deterministic JSON dataset to stdout or to a new explicit output path. It
   does not train, load a network, plot, or overwrite an existing output by
   default.

Robot data collection, LCM channels, calibration, controller launch, and
physical safety belong to [robot-deployment](../robot-deployment/SKILL.md), not
this sub-skill. Do not start a robot, publish LCM messages, SSH, transfer
artifacts, or run the repository's source-relative scripts as a prerequisite.

## Operating contract

- A valid source log has the shape `{"hardware_closed_loop": [config,
  infos]}` where `infos` is a chronological list of records. A portable JSON
  fixture may instead use `{"records": [...]}` or be a list of records; see
  [data format](references/data-format.md).
- Every record must provide 12 finite values for `joint_pos`,
  `joint_pos_target`, `joint_vel`, `tau_est`, and `torques`. The first three
  may be a singleton `(1, 12)` row as produced by the deployment logger;
  torque arrays may be `(12,)` or a singleton row.
- The extractor computes `error = joint_pos - joint_pos_target` and uses
  `[error[t], error[t-1], error[t-2], joint_vel[t], joint_vel[t-1],
  joint_vel[t-2]]` as six inputs for each joint. The target is `tau_est[t]`.
- The supplied artifact `resources/actuator_nets/unitree_go1.pt` is a
  TorchScript model contract, not a file to copy into this skill. Keep model
  weights and generated logs outside the skill tree.
- CPU model loading and a small forward pass are safe default checks. CUDA
  training and export are optional, explicitly bounded, and never run
  implicitly. Full training is not run by this skill.

## Bundled files

- [data-format.md](references/data-format.md) — log envelope, five required
  fields, 12-joint shape rules, history alignment, target, and split.
- [workflow.md](references/workflow.md) — no-plot extraction, CPU evaluation,
  optional CUDA training/export, architecture, and artifact handling.
- [api-reference.md](references/api-reference.md) — verified source helper
  signatures/defaults and semantics.
- [troubleshooting.md](references/troubleshooting.md) — actionable diagnosis
  for missing/incomplete data, `tau_est`, short history, shape/path issues,
  CUDA, overwrite, and headless plotting.
- [inspect_actuator_log.py](scripts/inspect_actuator_log.py) — read-only
  pickle/JSON validator with machine-readable summary and non-zero failures.
- [prepare_actuator_data.py](scripts/prepare_actuator_data.py) — deterministic
  six-feature/one-target JSON extractor with stdout or explicit safe output.

The scripts intentionally contain no source-repository-relative imports. They
are data checks and preparation helpers, not replacements for robot
collection or a training launcher.

## Verification boundary

The repository evidence was inspected from `scripts/actuator_net/utils.py`,
`train.py`, `eval.py`, `go1_gym_deploy/utils/logger.py`, the example log
format, `README.md`, and the existing TorchScript artifact contract. The
example artifact was loaded on CPU and accepted `(batch, 6)` input with
`(batch, 1)` output. The large example pickle was inspected for its envelope
and record shapes. Full actuator training, interactive plotting, CUDA
training, and physical deployment are not run or claimed here.
