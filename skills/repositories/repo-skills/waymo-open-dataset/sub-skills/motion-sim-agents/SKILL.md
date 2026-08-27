---
name: motion-sim-agents
description: "Guides Waymo Open Motion Dataset scenarios, occupancy flow,
  sim-agent and scenario-generation submissions, WOMD camera or LiDAR features,
  and rollout validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Motion and Sim Agents

Use this sub-skill for WOMD motion scenarios, `Scenario` protos, trajectory utilities, occupancy-flow parsing/grids/metrics, sim-agents or scenario-generation submissions, rollout validation, camera/LiDAR feature merging, and WDL-limited sim-agent metrics.

Read:

- [references/api-reference.md](references/api-reference.md) for verified occupancy, sim-agent, converter, and WOMD helper signatures.
- [references/workflows.md](references/workflows.md) for occupancy-flow metric flow, sim-agent validation, and WOMD camera/LiDAR merge recipes.
- [references/data-formats.md](references/data-formats.md) for `Scenario`, `ScenarioRollouts`, `JointScene`, occupancy tensors, and feature prerequisites.
- [references/troubleshooting.md](references/troubleshooting.md) for rollout counts, invalid ids, missing tracks, TFExample parsing, and WDL limitations.

Run [`scripts/check_sim_agent_submission.py`](scripts/check_sim_agent_submission.py) to print challenge types and config basics without data downloads.

Route generic metric wrapper mechanics to `metrics-evaluation`, V2 Parquet object assets to `v2-components`, and camera-only/E2E perception challenge content to `camera-and-segmentation`.
