---
name: setup-and-scenarios
description: "Install and diagnose OpenCDA, select a supported scenario, compose
  default-plus-override YAML, and run only when external CARLA or co-simulation
  prerequisites are ready."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# OpenCDA setup and scenarios

Use this sub-skill when a Researcher needs to prepare OpenCDA 0.1.3, inspect the
scenario CLI, choose a benchmark, or diagnose a configuration/prerequisite
failure. Start with [installation-and-prerequisites.md](references/installation-and-prerequisites.md),
then use [cli-reference.md](references/cli-reference.md),
[scenario-catalog.md](references/scenario-catalog.md), and
[configuration.md](references/configuration.md). Use
[scripts/check_scenario_cli.py](scripts/check_scenario_cli.py) for a static,
non-simulation repository check.

## Operating boundary

- Run commands from any directory by passing the repository root explicitly;
  do not assume the current directory is the checkout.
- `opencda.py --help` and static checks are local and safe. A benchmark run is
  not a smoke test: it needs a reachable CARLA server, matching CARLA Python
  API, installed maps, display/GPU resources as applicable, and a compatible
  scenario configuration.
- CARLA-only scenarios do not require SUMO. Co-simulation scenarios require a
  SUMO installation, `traci`, SUMO network/route files, and the co-simulation
  manager; they are outside the CARLA-only fast path.
- Keep `--apply_ml` off for the minimal baseline unless the selected scenario
  explicitly needs perception. The inspected environment did not verify
  PyTorch or YOLOv5, CARLA server, SUMO, ScenarioRunner, or YOLO runtime.
- Never launch a simulator from the static checker, and do not claim a
  scenario passed until its external backend and map are actually available.

## Procedure

1. Check the source tree and CLI without simulation:
   `python <repo-root>/opencda.py --help` and
   `python <skill-root>/scripts/check_scenario_cli.py --repo-root <repo-root>`.
2. Select a catalog entry and verify its CARLA version, map, ML, and traffic
   requirements. Prefer a CARLA-only entry with ML disabled for a dependency
   diagnosis.
3. Prepare the Python dependencies and CARLA API as documented. Verify
   `python -c "import carla"` separately from server connectivity.
4. Start the external CARLA server with the required map assets, then run the
   exact CLI command. Use synchronous mode; the configuration and Traffic
   Manager settings must agree.
5. Use the evaluation entry point described in [cli-reference.md](references/cli-reference.md)
   after the run, and preserve simulator logs separately from the skill.

For predictable failures, consult [troubleshooting.md](references/troubleshooting.md).
Docker is a reference deployment, not proof that the host has a working GPU,
X11/Vulkan path, CARLA server, or map assets; see
[container-deployment.md](references/container-deployment.md).
