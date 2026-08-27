---
name: evaluation-deployment
description: "Evaluate Dexbotic checkpoints in bounded benchmark workflows and
  plan safe simulator or robot deployment without unsafe hardware execution."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Dexbotic evaluation and deployment

Use this route for checkpoint evaluation, simulation benchmark boundaries, navigation workflows, and the data-only/bridge topology of SO-101, XLeRobot, and DOS-W1 deployments. Use [evaluation workflow](references/evaluation-workflows.md), [robot deployment](references/robot-deployment.md), and [troubleshooting](references/troubleshooting.md). HTTP request semantics belong to [inference-serving](../inference-serving/SKILL.md); dataset conversion/schema belongs to [data-preparation](../data-preparation/SKILL.md).

## Safe sequence

1. Verify checkpoint lineage, model family, camera mapping, action/state dimensions, norm stats, and action mode against the target benchmark or robot.
2. Validate data/config paths and run a single parser/help or synthetic request before starting a simulator. External simulators, benchmark assets, model weights, and long rollouts are optional and must not be implied by core-package verification.
3. For a robot, separate policy server, bridge, and robot client. Prove server health and a no-actuation request path first; never execute serial, camera, GPIO, network bridge, or physical-control code as a default skill action.
4. Treat action masks, FPS, chunk aggregation, and camera extrinsics as deployment contracts. Log them with the checkpoint.
5. Classify missing simulator, LeRobot, vendor, or hardware dependencies explicitly as optional-unverified rather than replacing them with a CPU claim.
