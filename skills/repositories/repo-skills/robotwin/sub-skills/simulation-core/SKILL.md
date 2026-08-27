---
name: simulation-core
description: "RoboTwin simulator bootstrap, task-class API, robot/camera
  configuration, and render troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# simulation-core

Use this skill for RoboTwin work that depends on the simulator core:
task classes, scene bootstrap, robot and camera wiring, embodiment config,
action helpers, render smoke checks, and simulation troubleshooting.
If you only have the generated skill tree, use the root [workspace bootstrapper](../../references/workspace-bootstrap.md) first to materialize a pinned public workspace before running simulator work.

## Owns
- `Base_Task` lifecycle and task subclass structure
- SAPIEN engine/scene/bootstrap and render refresh
- Robot, camera, and embodiment config interpretation
- Actor construction helpers and action helpers
- Render smoke and task-import smoke
- Simulation/debug troubleshooting for bootstrap, planning, and capture

## Route elsewhere
- Data download, normalization, and trajectory conversion → [`data-pipeline`](../data-pipeline/)
- Policy evaluation, XPolicyLab scheduling, and server setup → [`policy-eval`](../policy-eval/)

## Start here
1. Read [`references/api-reference.md`](references/api-reference.md) for the task and helper APIs.
2. Read [`references/configuration.md`](references/configuration.md) for task, camera, robot, and embodiment configs.
3. If you only need to confirm the render path, run [`scripts/check_render_smoke.py`](scripts/check_render_smoke.py).
4. If a task import fails before scene setup, check the asset prerequisites in [`references/troubleshooting.md`](references/troubleshooting.md).

## Native checks
- `render-smoke`: bundled SAPIEN bootstrap and camera capture smoke.
- `task-import-smoke`: import one representative task module after assets are present and verify its `Base_Task` path initializes cleanly.

## Good fits
- "How do I structure a new task class?"
- "Why does a grasp/place plan fail?"
- "Which config key controls cameras, embodiment, or eval step limits?"
- "Why does SAPIEN render bootstrap fail on this machine?"

## Not here
- Dataset download or HDF5 layout questions
- Policy-server, adapter, or multi-GPU eval questions
- LLM-based task generation or instruction writing

For deeper details, use the bundled references and keep simulator-specific debugging here.
