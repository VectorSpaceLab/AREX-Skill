---
name: smarts
description: "Use SMARTS 2.0.1 for multi-agent autonomous-driving simulation,
  Gymnasium environments, scenario generation, sensor and Envision workflows,
  agent-zoo/RL integration, and the scl command-line tools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SMARTS

Use this repo skill when the task involves **SMARTS** (Scalable Multi-Agent
Reinforcement Learning Training School), autonomous-driving simulation,
scenario maps and traffic, multi-agent Gymnasium environments, agent policies,
road/sensor observations, Envision replay, or the `scl` CLI.

## Operating contract

1. Identify the workflow before acting: environment lifecycle, scenario
   authoring, sensors/visualization, policy/RL/agent-zoo packaging, or CLI and
   external integrations.
2. Read the owning sub-skill and its linked references before writing code or
   commands. Keep paths to scenarios, models, records, and outputs explicit;
   do not assume a SMARTS source checkout.
3. Start with read-only import, signature, and CLI-help checks. Build or clean
   scenario artifacts, launch services, install optional stacks, and run
   training/benchmarks only after the user explicitly needs that operation and
   its inputs are validated.
4. Treat the core baseline as CPU-verified. Camera/Panda3D, Envision service,
   SUMO/TraCI, Ray/RLlib, Torch/TensorFlow, ROS, Waymo, Argoverse, Visdom, and
   downloaded datasets are optional capability boundaries; never infer their
   runtime success from a base import.
5. Keep a bounded run and deterministic seed for smoke tests. Close every
   environment/service/client that the task starts.

## Install and verify

For the core Python API:

```bash
python -m pip install "smarts"
python -c "import smarts; print('SMARTS import OK')"
```

Add only the extras required by the workflow:

```bash
python -m pip install "smarts[gymnasium]"       # Gymnasium environments
python -m pip install "smarts[camera-obs]"      # camera/grid/Panda3D paths
python -m pip install "smarts[envision]"        # Envision client/server path
python -m pip install "smarts[sumo]"             # SUMO-backed traffic/maps
python -m pip install "smarts[ray,rllib]"        # optional Ray/RLlib stack
```

The exact extra names and compatible versions can change; inspect installed
metadata and run the shared diagnostic before relying on an optional branch:
[`scripts/check_smarts_install.py`](scripts/check_smarts_install.py). The
prepared baseline verified package `smarts` 2.0.1, core imports, Gymnasium,
OpenDRIVE, Envision/Panda3D imports, and `scl` help on Python 3.11. It did not
verify external SUMO/ROS/Waymo/Argoverse services or RL training stacks.

## Route the task

| User intent | Read first | Typical deliverable |
|---|---|---|
| Create/reset/step a single or multi-agent simulator, configure interfaces, observations, actions, rewards, or controllers | [`simulation-environments`](sub-skills/simulation-environments/SKILL.md) | Bounded `HiWayEnvV1`/parallel environment loop and policy contract |
| Define maps, traffic, missions, social actors, bubbles, friction, or replay histories; generate or validate scenario assets | [`scenario-studio`](sub-skills/scenario-studio/SKILL.md) | `smarts.sstudio` DSL, deterministic generation, layout validation |
| Add lidar, grid/RGB/occlusion/signal sensors, camera rendering, Envision recording, or replay | [`sensors-visualization`](sub-skills/sensors-visualization/SKILL.md) | Sensor interface, renderer/service probe, record inspection |
| Implement a policy, `AgentSpec`, locator, social agent, bubble, RLlib adapter, or benchmark inference package | [`rl-agent-zoo`](sub-skills/rl-agent-zoo/SKILL.md) | Importable/versioned agent package and optional RL integration plan |
| Use `scl`, diagnostics, scenario build/clean, benchmarks, zoo commands, SUMO/TraCI, Waymo, OpenDRIVE, or ROS boundaries | [`cli-integrations`](sub-skills/cli-integrations/SKILL.md) | Safe command plan, prerequisite probe, and recovery steps |

Cross-route handoffs are deliberate: scenario-studio owns authoring while
cli-integrations owns `scl scenario build`; simulation-environments owns the
reset/step contract while sensors-visualization owns rendered observation
prerequisites; rl-agent-zoo owns policies while CLI owns zoo/benchmark commands.

## Core safety rules

- A scenario must already have the generated map/traffic artifacts before a
  core environment smoke. Use scenario-studio and then the CLI route to build
  it; do not silently substitute a different map.
- In multi-agent mode, observations and actions contain only currently active
  agents. An empty active-agent dictionary can be a valid intermediate state;
  keep stepping with `{}` until the global done flag or the bound is reached.
- Match policy outputs to `env.action_space[agent_id]`; do not guess action
  tuples from an interface name. Use `space.contains(action)` when debugging.
- Use `headless=True` for CPU checks. Image observations can require the
  camera extra and a display/offscreen backend, and can dominate step time.
- `scl --help`, `scl scenario --help`, and `scl run --help` are safe first
  checks. `--clean`, `--auto-install`, server startup, benchmark execution,
  and external-service commands have side effects or trust boundaries.

Read [`references/troubleshooting.md`](references/troubleshooting.md) for
cross-cutting installation, optional-extra, path/configuration, port, and
lifecycle failures. Read [`references/repo-provenance.md`](references/repo-provenance.md)
before deciding whether this graph is stale for another SMARTS checkout.
