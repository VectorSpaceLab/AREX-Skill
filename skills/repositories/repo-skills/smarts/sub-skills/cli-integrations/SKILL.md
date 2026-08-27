---
name: cli-integrations
description: "Operate SMARTS through the scl Click CLI, build and run scenarios
  safely, diagnose configuration and optional integrations, and manage
  SUMO/TraCI, dataset, benchmark, zoo, and Envision boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SMARTS CLI and integrations

Use this route when the task is about the installed `scl` command, scenario
artifact lifecycle, integration prerequisites, diagnostics, benchmarks, zoo
workers, or external map/traffic/data systems. Start with read-only help and
package probes; do not install packages or start services as a diagnostic side
effect.

## Operating contract

- Run commands from the user's project directory and pass paths that exist from
  that directory. Click validates most path arguments before SMARTS runs.
- Treat scenario `build`, `build-all`, `clean`, Waymo `export`, zoo `build`/
  `install`, diagnostics, benchmarks, and server commands as potentially
  mutating or long-running. Inspect help and use a disposable copy/output first.
- Use [references/cli-reference.md](references/cli-reference.md) for the
  verified command tree and exact options.
- Use [references/configuration-and-diagnostics.md](references/configuration-and-diagnostics.md)
  for install extras, configuration precedence, diagnostic behavior, and safe
  benchmark/container practice.
- Use [references/optional-integrations.md](references/optional-integrations.md)
  to distinguish importable SMARTS core from external data, packages, and
  system services.
- For SUMO and TraCI port ownership, local versus central mode, and recovery,
  read [references/sumo-traci.md](references/sumo-traci.md).
- Apply the cross-surface recovery table in
  [references/troubleshooting.md](references/troubleshooting.md).

## Verified command entry point

The package exposes `scl` as its console entry point. The verified top-level
commands are `benchmark`, `diagnostic`, `envision`, `run`, `scenario`, `waymo`,
and `zoo`. Confirm the installed version rather than assuming this tree is
current:

```bash
scl --help
scl scenario --help
scl run --help
```

The safe bundled checker repeats those bounded help calls without a shell:
[check_scl_help.py](scripts/check_scl_help.py). Optional dependency and
executable availability can be reported with
[check_optional_integrations.py](scripts/check_optional_integrations.py).

## Choose the smallest workflow

1. **Scenario preparation:** use `scl scenario build <scenario>` or
   `build-all <scenarios>`. Use `--seed` for repeatable generation. Add
   `--clean` only when intentionally replacing generated artifacts. Detailed
   scenario DSL, map specifications, missions, traffic, and source-vs-build
   layout belong to [the scenario-studio route](../scenario-studio/SKILL.md).
2. **Experiment execution:** use `scl run <script> [SCRIPT_ARGS...]`. Add
   `--envision --envision_port PORT` only when a local Envision server is
   wanted. The child script receives the remaining arguments; it must arrange
   its own environment/scenario semantics. See the run safety notes in the
   CLI reference.
3. **Replay/visualization:** `scl scenario replay` sends `*.jsonl` records to
   an Envision websocket endpoint. Envision data formatting, replay records,
   sensors, and rendering belong to [the sensors-visualization route](../sensors-visualization/SKILL.md).
4. **Health/performance:** `scl diagnostic run <scenarios...>` is a bounded
   diagnostic workflow only when its diagnostic scenarios and optional
   dependencies are present. It is not a substitute for a benchmark or a
   short import check.
5. **Benchmarks/zoo:** list before running. Treat `--auto-install`, custom
   benchmark listings, zoo installation, policy builds, manager startup, and
   remote workers as explicit trust and mutation boundaries. RL policy
   implementation and AgentSpec/locator details belong to
   [the rl-agent-zoo route](../rl-agent-zoo/SKILL.md).
6. **Dataset/map integrations:** use the Waymo subcommands only with a
   Scenario-proto TFRecord and a deliberate export directory. Argoverse,
   OpenDRIVE, ROS, and SUMO-backed maps are optional integration paths, not
   proof that the base CLI is broken when absent.

## Configuration and ports

SMARTS configuration resolves `SMARTS_<SECTION>_<OPTION>` environment
variables before an engine INI file and then built-in defaults. The default
SUMO central host/port are `localhost:8619`; the default TraCI serve mode is
`local`. Envision CLI defaults to port `8081`, zoo manager to `7432`, and
Visdom (if enabled by another workflow) to `8097`. Check for listeners before
starting a service and choose an unused per-run port; do not kill an unrelated
process merely to free a port.

A core CPU installation is sufficient for CLI help, non-rendered scenario
operations, and normal package imports. The prepared inspection environment
verified SMARTS 2.0.1, Click help, core imports, Envision/Panda3D imports, and
OpenDRIVE imports. It did **not** include external SUMO, ROS, Waymo, Argoverse,
Ray/RLlib, Torch, or TensorFlow stacks or downloaded datasets. Missing these
must be reported as optional/unverified, not silently worked around.

## Boundaries and escalation

- Route scenario authoring and generated-layout errors to
  [scenario-studio](../scenario-studio/SKILL.md); this route only explains how
  to invoke its CLI boundary and protect generated files.
- Route Envision protocol/data/replay API and sensor configuration to
  [sensors-visualization](../sensors-visualization/SKILL.md).
- Route policy code, locators, social agents, RLlib/Ray, and training to
  [rl-agent-zoo](../rl-agent-zoo/SKILL.md).
- Do not auto-install, launch a long-lived SUMO/TraCI/Envision/ROS/zoo service,
  run a benchmark, or execute a stress/memory/long-determinism suite while
  merely diagnosing an installation. Report the missing prerequisite and the
  smallest user-controlled next step instead.
