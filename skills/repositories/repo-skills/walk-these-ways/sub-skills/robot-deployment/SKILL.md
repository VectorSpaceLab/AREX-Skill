---
name: robot-deployment
description: "Prepare and review Unitree Go1 deployment artifacts, LCM
  contracts, RC command and gait profiles, calibration and emergency gates,
  logging, and network/container prerequisites without actuating a robot or
  mutating a deployment host."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Robot Deployment

Use this sub-skill for **deployment preparation and review only**. It distills the
repository's Go1 low-level controller boundary: the policy/checkpoint contract,
LCM observations and targets, RC commands and gait profiles, calibration,
emergency behavior, logging, and the Jetson/container/network prerequisites.

## Safety gate — read before every other step

1. **Do not actuate.** This skill never publishes LCM targets, starts the Unitree
   SDK, launches a controller, loads a Docker image, transfers files, changes a
   route/interface, or runs the architecture-specific `lcm_position` binary.
   It has no bundled launcher.
2. **Real end-to-end deployment is `BLOCKED_REQUIRED_BACKEND`** unless a human
   operator supplies a Unitree Go1 Edu, a compatible onboard computer or approved
   external controller, the matching SDK/LCM runtime, a physically controlled test
   area, and explicit approval for each unsafe step. Static artifact, schema, and
   read-only diagnosis work can continue without hardware.
3. Before any operator-run activity, use [Safety](references/safety.md): suspend
   the robot, clear the area, enter damping mode, keep people/obstacles away, do
   not attach Ethernet/USB at the rear during initial calibration or a new-policy
   test, and confirm the operator has an emergency stop plan. The README marks
   this research code as use-at-your-own-risk.
4. Every transfer, SDK start, container start, calibration, and control-loop
   launch is **human-approved and unsafe**. This skill provides an order and
   gates, not copy-paste execution. Stop on any missing prerequisite or
   unexpected motion.

## Route and operating workflow

1. Read [Safety](references/safety.md), then [Controller workflow](references/controller-workflow.md).
2. Route policy labels, `parameters.pkl`, observation-history shape, TorchScript
   export, and checkpoint repair to `training-and-policy`; route actuator fitting
   and deployment-log sample preparation to `actuator-network`.
3. Validate a candidate policy directory with the read-only
   `scripts/validate_policy_artifacts.py`. It checks names and metadata only; it
   never deserializes a pickle, loads TorchScript, runs inference, or enters a
   control loop.
4. Check [LCM contract](references/lcm-contract.md), then use
   `scripts/diagnose_network.py` for a read-only local interface/IP/multicast
   report. A report is not proof that a robot is reachable and does not modify
   the host.
5. Review [Installation and transfer](references/installation-and-transfer.md)
   and [Container runtime](references/container-runtime.md). The operator must
   independently approve credentials, disk, architecture, image provenance,
   network configuration, and rollback before using SSH/rsync/Docker/SDK tools.
6. Use [Troubleshooting](references/troubleshooting.md) for failures. If a
   required hardware/backend, generated message module, matching binary, or
   checkpoint component is unavailable, report the blocker rather than trying a
   side effect.

## Contracts worth preserving

- The deployment script constructs an LCM agent and RC profile at `0.02 s`
  (`50 Hz`) and wraps the observation in a history buffer before calling the
  exported policy. The effective agent step is
  `control.decimation * sim.dt`; it must agree with the policy's training
  contract.
- The policy's first twelve outputs are joint actions. The deployment agent
  applies action scale, hip-scale reduction, default joint pose, and the source
  permutation before forming a `pd_tau_targets` message. Do not hand-edit this
  mapping; see the controller and LCM references.
- State input is assembled from gravity, scaled commands, joint position/velocity
  deltas, prior actions, optional velocity/yaw/contact/clock/height fields, and
  the configured observation history. A configuration mismatch is a hard stop,
  not an invitation to guess.
- `udpm://239.255.76.67:7667?ttl=255` is the source LCM URL. State subscriptions
  and the output target channel are documented, but this skill never subscribes
  or publishes at runtime.

## Safe validation outputs

A useful handoff consists of: the exact candidate artifact directory; the
validator's pass/fail report; the policy config and expected observation/action
shapes; the planned SDK → controller order; LCM URL/interface evidence; human
safety approval; and rollback/stop criteria. No private environment paths,
credentials, copied model weights, generated logs, or vendor binaries belong in
this skill.

## References

- [safety.md](references/safety.md) — physical, damping, calibration, PowerProtect, and emergency gates.
- [controller-workflow.md](references/controller-workflow.md) — transfer/controller order, policy contract, mapping, timing, RC/gaits, calibration, and logging.
- [lcm-contract.md](references/lcm-contract.md) — URL, channels, schemas, state fields, camera caveat, and architecture boundary.
- [installation-and-transfer.md](references/installation-and-transfer.md) — human-run SSH/rsync/Docker sequence, prerequisites, checkpoints, and rollback.
- [container-runtime.md](references/container-runtime.md) — Jetson L4T, privileged host-network NVIDIA Docker, ARM, and display assumptions.
- [troubleshooting.md](references/troubleshooting.md) — known architecture, network, dependency, storage, checkpoint, tilt, and camera failures.

## Evidence boundary

This operating context was distilled from the repository README deployment and
debug sections, `go1_gym_deploy/scripts/deploy_policy.py`,
`utils/deployment_runner.py`, `utils/command_profile.py`,
`utils/cheetah_state_estimator.py`, `utils/network_config_unitree.py`,
`utils/logger.py`, `envs/lcm_agent.py`, `envs/history_wrapper.py`, generated
LCM schemas, and Docker/autostart/installer/transfer files. The shell scripts
are evidence of side effects, not runtime helpers. No claim here substitutes
for Unitree safety documentation or a hardware-qualified operator.
