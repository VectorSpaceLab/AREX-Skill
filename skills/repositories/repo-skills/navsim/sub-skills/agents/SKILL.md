---
name: agents
description: "Implement and debug NAVSIM rule-based, privileged, learned,
  TransFuser, and latent TransFuser agents while preserving sensor, trajectory,
  feature-builder, and checkpoint contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NAVSIM agents

Use this route when an agent must be selected, implemented, trained, loaded, or
troubleshot. It covers the `AbstractAgent` interface, rule-based and privileged
baselines, ego-status and TransFuser/LTF learned agents, sensor history, local
trajectory sampling, feature/target builders, and checkpoint loading.

## Route by intent

- **Interface or API design:** read [API reference](references/api-reference.md).
- **Sensor selection or output shape:** read
  [trajectory and sensors](references/trajectory-and-sensors.md).
- **Baseline choice or learned-agent extension:** read
  [baselines](references/baselines.md).
- **An error or failed run:** read [troubleshooting](references/troubleshooting.md)
  and run the safe validator before touching data or launching a workload.

## Required operating rules

1. Subclass `AbstractAgent`, expose a stable `name()`, initialize once per
   worker, return a deliberate `SensorConfig`, and return local rear-axle BEV
   `(x, y, heading)` poses in a `Trajectory`.
2. Treat the trajectory sampling object as part of the model contract. The
   repository default requests a 4-second horizon sampled every 0.5 seconds;
   evaluation uses a 4-second, 0.1-second proposal. Do not silently change one
   to satisfy the other.
3. A submission receives `AgentInput`, not an annotated `Scene`. Keep
   `requires_scene=False` for submission agents; the human/privileged baseline
   is useful for analysis but is prohibited in submission creation.
4. Choose sensors explicitly. TransFuser uses the current front camera trio and
   current LiDAR by default; latent TransFuser replaces the LiDAR branch with a
   learned latent tensor and must not request or build a LiDAR feature.
5. Learned agents must keep feature-builder keys, target-builder outputs,
   `forward()` output (including `"trajectory"` with shape `[B, T, 3]`), loss,
   optimizer, and checkpoint key namespaces mutually compatible.

## Safe verification

Run the bundled [agent contract validator](scripts/validate_agent_contract.py):

```bash
python scripts/validate_agent_contract.py
python scripts/validate_agent_contract.py --help
```

The validator uses synthetic arrays and sensor configurations only. It does not
require a dataset, maps, checkpoints, downloads, submission credentials, or a
benchmark. Add `--module path/to/your_agent.py` to inspect importable agent
classes without instantiating or running them; use `--strict` when missing
optional NAVSIM dependencies should fail the check.

Keep training, scoring, submission generation, and dataset access on their
respective workflow routes. This sub-skill explains how an agent participates
in those workflows but does not launch them by default.
