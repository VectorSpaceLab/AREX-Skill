---
name: benchmark-integrations
description: "Guides RoboVerse benchmark metadata, dataset and demo conversion,
  and optional LIBERO, ManiSkill, MJLab, robosuite, RobotWin, and SimplerEnv
  integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Benchmark Integrations

Use this route when the task mentions benchmark task specs, dataset layouts,
LIBERO, ManiSkill, MJLab, robosuite, RobotWin, SimplerEnv, passthrough,
replay, demo conversion, or cross-framework evaluation.

## Route

1. Read [workflows.md](references/workflows.md) to select metadata-only,
   local-fixture conversion, replay, passthrough, or native integration.
2. Read [data-formats.md](references/data-formats.md) before converting or
   replaying data. Establish task/robot/simulator/camera/action identity and
   episode boundaries first.
3. Treat each external stack as an optional backend with its own dependency,
   asset, license, data, display, GPU, and version gate. The package's CPU
   import does not verify a native integration.
4. Run the tiny fixture or inventory path before any download, rollout, render,
   sweep, or policy evaluation. Record PASS, SKIP_NOT_SELECTED, or the actual
   blocker; never disguise missing assets as a test failure.
5. Use [troubleshooting.md](references/troubleshooting.md) for locator, format,
   passthrough, replay, and backend failures.

The `BenchmarkTaskSpec` metadata API is lightweight and robot-agnostic; use it
for planning even when a native benchmark backend is unavailable. Task changes
route to [task-development](../task-development/SKILL.md); measured parity
routes to [parity-and-tooling](../parity-and-tooling/SKILL.md).
