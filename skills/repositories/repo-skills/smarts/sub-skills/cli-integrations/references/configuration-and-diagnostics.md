# Configuration, diagnostics, and safe operations

## Installation boundaries

The `scl` console entry point comes from the base package. Select extras for
the workflow instead of installing an all-inclusive environment:

| Need | Extra(s) evidenced by the package | What it does not prove |
|---|---|---|
| Core CLI, non-rendered simulation, scenario build | base package | SUMO, ROS, dataset access, or RL stacks |
| Camera/Panda3D rendering | `camera-obs` | A display server or successful full renderer behavior |
| Envision server/client | `envision` | A browser, websocket reachability, or replay data |
| Gymnasium environment | `gymnasium` | A valid scenario or an agent policy |
| OpenDRIVE maps | `opendrive` | That a particular `.xodr` file is valid |
| SUMO traffic/maps | `sumo` | A running SUMO binary, usable TraCI port, or map compatibility |
| Waymo Motion Dataset | `waymo` | Downloaded Scenario-proto TFRecords or a supported protobuf/data version |
| Argoverse 2 | `argoverse` | Downloaded map/scenario files or network credentials |
| Diagnostic reports | `diagnostic` | A short smoke test; it performs episodes and writes reports |
| ROS integration | `ros` | A ROS installation, master, message packages, or running nodes |
| Ray/RLlib and training | `ray`, `rllib`, `torch`, `train` | Correct algorithm/config/checkpoint compatibility |
| Visdom | `visdom` | A running Visdom server |

The prepared inspection environment used base, camera, Envision, Gymnasium,
OpenDRIVE, and test extras. It passed `pip check`, package/import smoke, and
CLI help. It intentionally did not install `sumo`, `ros`, `waymo`,
`argoverse`, `ray`, `rllib`, `torch`, `train`, `visdom`, or `diagnostic`.
This is an environment fact, not a recommendation to install everything.

## Configuration resolution

SMARTS's default `config()` looks for an engine INI in this order: an explicit
path (by default `./smarts_engine.ini`), the user engine configuration, the
system engine configuration, and the package fallback. For each setting, the
`SMARTS_<SECTION>_<OPTION>` environment variable takes precedence over the INI
value and built-in default. Values are cast according to the requested API;
boolean strings must parse as a Python truthy/false value rather than relying
on `bool("false")` behavior.

Relevant defaults include:

| Section/key | Default | Operational meaning |
|---|---:|---|
| `sumo.central_host` | `localhost` | Host for central TraCI allocation |
| `sumo.central_port` | `8619` | Central TraCI management port |
| `sumo.traci_serve_mode` | `local` | Local SUMO process unless set to `central` |
| `traffic.traci_retries` | `5` | Connection retry budget for TraCI startup |
| `core.debug` | `False` | Core diagnostic logging switch |
| `visdom.enabled` | `False` | Optional Visdom path |
| `visdom.hostname` / `port` | `http://localhost` / `8097` | Optional Visdom endpoint |

For example, central mode uses `SMARTS_SUMO_TRACI_SERVE_MODE=central`,
`SMARTS_SUMO_CENTRAL_HOST=HOST`, and `SMARTS_SUMO_CENTRAL_PORT=PORT`. Do not
mix a configuration file and environment variables unintentionally; print or
inspect the effective configuration in the same process that will run SMARTS.
See [sumo-traci.md](sumo-traci.md) for the startup sequence and port checks.

## Diagnostics

`scl diagnostic run <scenario-name...>` invokes the packaged diagnostic runner.
The runner builds each selected diagnostic scenario, creates a headless
Gymnasium environment with no agent interfaces, resets repeatedly, measures
step throughput, and writes a timestamped Markdown report and plot beneath the
packaged diagnostic reports directory. The available families include varying
numbers of social agents, replay actors, SUMO actors, roads, and mixed actors.

Use it only when:

- the `diagnostic` dependencies are installed;
- the selected names are valid packaged diagnostic cases;
- the user explicitly wants a performance report; and
- the run can spend the required episode/time budget and write report files.

It is not a proof of deterministic behavior, memory safety, renderer health, or
SUMO availability. The long determinism, memory-growth, frame-rate,
benchmark, stress, and system-service suites were intentionally not selected as
native smoke checks. Start with `scl diagnostic run --help` and a single tiny
case; do not infer performance from CLI help.

## Benchmark and container safety

`benchmark list` is the read-only first step. A benchmark listing contains an
entry point, parameters, and optional requirements. `benchmark run` can execute
that entry point, and `--auto-install` can install its requirements. Never use
`--auto-install` with an unknown listing or a listing copied from an untrusted
source. Pin the benchmark and agent locator, record the listing used, and run
in an isolated environment.

Container examples map a host project into a container and expose Envision's
8081 port. Preserve the same path visibility inside the container and build
scenarios before running an experiment. Container startup, host package setup,
XQuartz/X11 setup, and Singularity/Apptainer installation are deliberately not
bundled as helpers because they mutate host or system state. Prefer an
already-reviewed image and a disposable bind mount; do not run setup installers
as an import diagnostic.

## Make and CI evidence

The repository's safe command vocabulary reinforces the CLI boundary: the
`build-all-scenarios` target calls `scl scenario build-all scenarios`,
`build-sumo-scenarios` scopes the same operation to SUMO scenarios,
`build-sanity-scenarios` uses `scl scenario build --clean` for two known cases,
and `run` builds one scenario before invoking a Python script. The `sanity-test`
target includes a focused example and core checks, while the benchmark target
runs a benchmark test suite after building all scenarios.

CI deliberately separates optional/expensive surfaces. Base tests exclude or
skip benchmark, memory-growth, long-determinism, selected renderer, RL/training,
Waymo, and Argoverse cases; a macOS workflow installs SUMO separately and sets
`SUMO_HOME`; learning CI installs Ray/RL/training extras. These commands are
evidence of workflow boundaries, not a reason to run their full suites during
an installation probe.

## Safe inspection recipe

```bash
python -c 'import smarts, cli.cli; print(smarts.VERSION)'
scl --help
scl scenario --help
scl run --help
python scripts/check_optional_integrations.py
```

The bundled helpers do not install, write, launch a server, connect to a remote
service, or run a benchmark. For a failed optional probe, capture the missing
extra/executable and continue with the core route unless that integration is a
stated requirement.
