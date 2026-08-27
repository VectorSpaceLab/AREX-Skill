---
name: setup-and-cluster
description: "Guides agents through RLinf installation target selection,
  environment probes, Ray cluster startup, Hydra cluster configuration,
  component placement, heterogeneous node groups, execution modes, and scheduler
  API orientation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# setup-and-cluster

Use this sub-skill when the task is to prepare, inspect, or explain RLinf runtime setup: choosing an install target, verifying that `rlinf`/Ray/Torch/backends import, starting or checking a Ray cluster, reading `cluster:` YAML, planning component placement, reasoning about heterogeneous node groups, or orienting around the scheduler API.

Do **not** use this sub-skill for task-specific training/evaluation commands, metrics/checkpoints/debug sessions, or adding new RLinf models/environments/algorithms. Route those to the sibling sub-skills `embodied-workflows`, `reasoning-agent-workflows`, `operations-evaluation-debugging`, or `extension-development` as appropriate.

## Read these bundled references

- [Installation and cluster readiness](references/installation-and-cluster.md) — install target choices, Docker-vs-UV decisions, safe probes, and single-/multi-node Ray procedures.
- [Configuration and placement](references/configuration-and-placement.md) — Hydra basics, `cluster.num_nodes`, short and node-group placement syntax, execution modes, and heterogeneous hardware planning.
- [Scheduler API mental model](references/scheduler-api.md) — `Cluster`, `Worker`, `WorkerGroup`, placement strategies, channels, and how config becomes Ray actors.
- [Troubleshooting](references/troubleshooting.md) — missing Ray, stale Ray environment variables, network/NIC issues, placement over-allocation, optional accelerator packages, and Python dependency problems.

## Use these bundled scripts

Run scripts from this sub-skill directory or by absolute path; they do not depend on the original RLinf checkout unless you explicitly pass `--repo-root`.

```bash
python scripts/rlinf_env_probe.py --help
python scripts/rlinf_env_probe.py --json
python scripts/render_cluster_plan.py --help
python scripts/render_cluster_plan.py path/to/config.yaml
```

- [`scripts/rlinf_env_probe.py`](scripts/rlinf_env_probe.py) safely probes Python, package imports, Ray command/status, relevant RLinf environment variables, and CUDA/Torch availability.
- [`scripts/render_cluster_plan.py`](scripts/render_cluster_plan.py) parses a YAML config without importing RLinf and summarizes `cluster.num_nodes`, `component_placement`, `node_groups`, `env_configs`, and hardware blocks.

## Operating rules

1. Verify before advising: run the bundled environment probe, `ray status`, or the placement-render script when the user gives an environment/config to inspect.
2. Treat installation as a planning decision unless the user explicitly authorized environment creation. This sub-skill describes install selectors but should not launch dependency installation by default.
3. Set `RLINF_NODE_RANK` before `ray start` on every node. If the value or Python environment changes after Ray starts, stop and restart Ray on that node.
4. Keep `cluster.num_nodes` equal to the real joined node count and use zero-based node ranks.
5. For heterogeneous clusters, prefer explicit `node_groups` and `component_placement` node-group form; reserve short form for homogeneous accelerator layouts.
6. Never call `ray.init()` before RLinf's `Cluster` in driver code; RLinf owns the Ray namespace and manager actors.

