# ScenarioRunner and OpenSCENARIO

## Optional integration

OpenCDA's `openscenario_carla` entry point imports `scenario_runner`, starts a
ScenarioRunner process, waits for the hero vehicle and configured actor count,
wraps the hero with an OpenCDA vehicle manager, and then runs the OpenCDA
control loop while ScenarioRunner owns the scenario actors. The YAML route
contains a `scenario_runner` block with a CARLA town, scenario name, actor
count, config XML, optional additional scenario module, host/port, timeout,
and runner flags. The XML and Python scenario paths must be valid in the
consumer's environment; do not copy development-machine absolute paths into a
portable skill configuration.

The integration is optional and version-sensitive. Match ScenarioRunner to the
CARLA release, make the ScenarioRunner root importable, expose the compatible
CARLA Python API, and follow the upstream ScenarioRunner/OpenSCENARIO setup
instructions. The repository documentation describes `SCENARIO_RUNNER_ROOT`,
`PYTHONPATH`, and an import probe; use equivalent paths for the target machine,
not paths from a source checkout.

## Safe setup sequence

1. Confirm the CARLA server version and Python client compatibility.
2. Install or otherwise expose the matching ScenarioRunner release and its
   dependencies; verify `import scenario_runner` in the intended interpreter.
3. Confirm the OpenSCENARIO XML, any custom scenario module, town, hero role,
   and expected actor count agree.
4. Start CARLA and only then run the OpenCDA scenario entry point. Keep one
   synchronous tick owner; ScenarioRunner and OpenCDA must not both advance the
   world independently.
5. In the handoff loop, wait for the hero before creating its vehicle manager;
   update and apply OpenCDA controls once per committed frame.
6. Always destroy the OpenCDA manager and ScenarioRunner in cleanup, including
   error paths.

## Limits and distinction

ScenarioRunner is not the CARLA-SUMO bridge. An OpenSCENARIO file describes
scenario events/actors for ScenarioRunner; it does not create SUMO map triplets
or establish V2X semantics. This repository's optional route was not executed
in inspection: ScenarioRunner, its scenario XML runtime, and a CARLA server
were unavailable. Treat import/help checks as setup checks, not scenario
validation. If `scenario_runner` is missing, do not silently fall back to a
co-simulation or CARLA-only workflow; select the intended backend explicitly.
