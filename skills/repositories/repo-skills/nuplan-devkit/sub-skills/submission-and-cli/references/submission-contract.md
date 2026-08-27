# Submission contract

This contract describes the v1.2.2 submission boundary evidenced by the
Hydra launcher, `AbstractPlanner`, gRPC servicer, converters, container
wrapper, and competition guide. It is intentionally separate from the full
simulation API.

## Static manifest format

The bundled checker consumes a JSON object. It is a declaration and sample
output record, not a replacement for a planner run. Use repository-relative
paths and representative trajectory points:

```json
{
  "entrypoint": "nuplan/entrypoint_submission.sh",
  "changed_files": [
    "nuplan/planning/simulation/planner/my_planner.py",
    "nuplan/planning/script/config/simulation/planner/my_planner.yaml"
  ],
  "planner_config": {
    "horizon_seconds": 10.0,
    "sampling_time": 0.25
  },
  "current_time_us": 1000000,
  "trajectory": [
    {"x": 0.0, "y": 0.0, "heading": 0.0, "time_us": 1250000},
    {"x": 1.0, "y": 0.0, "heading": 0.0, "time_us": 9250000}
  ]
}
```

`changed_files` is checked against the five protected paths and the protected
files under `--root` are checked against the v1.2.2 base digests. The checker
also verifies that the entrypoint exists and mentions both
`run_submission_planner.py` and `planner=`; that the declared planner horizon
is at least 8 seconds and its sampling time is positive and no slower than 1
Hz; and that representative output points contain finite x/y/heading values,
an integer-microsecond `time_us` signal (the checker also accepts the explicit
`timestamp` alias), strictly increasing times, at least two points, and an
8-second span between the first and last timestamp. When `current_time_us` is
supplied, the first point may equal it but must not be earlier. The JSON file
is not required to be inside the image and should not contain secrets.

Run it from the repository root:

```bash
python skills/disco/nuplan-devkit/sub-skills/submission-and-cli/scripts/check_submission_manifest.py \
  --root . --manifest submission-manifest.json
```

A pass means static declarations are coherent; it does not run the planner,
inspect the full output distribution, build Docker, or contact a remote
service.

## Planner-side interface

A submission planner is an `AbstractPlanner` implementation. The current
Python signatures are:

```python
AbstractPlanner.initialize(self, initialization: PlannerInitialization) -> None
AbstractPlanner.observation_type(self) -> Type[Observation]
AbstractPlanner.compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory
AbstractPlanner.compute_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory
```

The value objects are:

```python
PlannerInitialization(
    route_roadblock_ids: List[str],
    mission_goal: StateSE2,
    map_api: AbstractMap,
)

PlannerInput(
    iteration: SimulationIteration,
    history: SimulationHistoryBuffer,
    traffic_light_data: Optional[List[TrafficLightStatusData]] = None,
)
```

`compute_trajectory` wraps `compute_planner_trajectory`, records runtime, and
re-raises planner exceptions. The submission boundary must therefore return a
non-empty `AbstractTrajectory` whose sampled states have global rear-axle pose
and time values. An `InterpolatedTrajectory` also requires at least two states
with distinct, increasing timestamps. A planner intended for this challenge
should keep
`requires_scenario = False`; scenario-dependent oracle planners are outside
the submission contract.

The competition guide sets these output requirements:

- at least 8 seconds of future horizon;
- at least 2 trajectory steps;
- each point carries global-frame x and y for the ego rear-axle center,
  global-frame heading, and a timestamp;
- the competition runs at 10 Hz, uses up to a 15-second rollout, and gives a
  one-second budget per simulation iteration;
- the input history can include up to two seconds of past scene information.

The guide's metrics text also states a one-Hz minimum planning frequency and a
six-second metric horizon in its metric-specific discussion. Treat the stricter
submission table (8 seconds) as the preflight floor and prefer a longer
trajectory when the planner can provide one. Validate the actual timestamp
spacing and monotonicity rather than inferring horizon from a config name.

## Hydra launcher wiring

The submission image's entrypoint invokes the submission planner launcher.
The launcher:

1. calls the package path setup helper;
2. resolves `NUPLAN_HYDRA_CONFIG_PATH` or the bundled simulation config path;
3. composes `default_submission_planner`;
4. seeds from `cfg.seed`;
5. constructs `SubmissionPlanner(planner_config=cfg.planner)`;
6. calls `serve()`.

The default config requires both `output_dir` and `planner` overrides. The
planner config is instantiated by `build_planners` inside the servicer. The
reference simple planner config has this shape:

```yaml
simple_planner:
  _target_: nuplan.planning.simulation.planner.simple_planner.SimplePlanner
  _convert_: all
  horizon_seconds: 10.0
  sampling_time: 0.25
  acceleration: [0.0, 0.0]
  max_velocity: 5.0
  steering_angle: 0.0
```

A custom config should use a fully qualified `_target_`, match the constructor
arguments, and be selected by the intended planner override. Keep config and
asset paths inside the Docker build context. Do not solve a Hydra target
failure by editing the submission server or generated protocol.

The checked-in entrypoint uses this pattern inside the image:

```bash
conda run -n <environment> --no-capture-output python -u \
  nuplan/planning/script/run_submission_planner.py \
  output_dir=<output-dir> planner=simple_planner
```

The environment launcher is part of this image's entrypoint; preserve a
working equivalent if the image is customized. The important arguments are
the launcher script, `output_dir`, and `planner` values, not a host-specific
shell command. The normal remote planner config is
`remote_planner`, with target
`nuplan.planning.simulation.planner.remote_planner.RemotePlanner`.

## gRPC service and message flow

The protocol exposes one service with two RPCs:

```text
InitializePlanner(PlannerInitializationLight) -> Empty
ComputeTrajectory(PlannerInput) -> Trajectory
```

Initialization contains:

- `route_roadblock_ids: repeated string`;
- `mission_goal: StateSE2 { x, y, heading }`;
- `map_name: string`.

The client maps `PlannerInitialization` to this message and uses the map API's
`map_name`. Initialization must complete before computation. The server builds
exactly one planner from the Hydra config, resolves the named map, initializes
all map layers, resets the rolling history buffer, and invokes the planner's
`initialize` method.

A `PlannerInput` contains:

- `simulation_iteration { time_us, index }`;
- `simulation_history_buffer { ego_states, observations, sample_interval }`;
- repeated `traffic_light_data` messages.

History state and observation elements are serialized bytes. The servicer
unpickles them and either creates a `SimulationHistoryBuffer` or extends the
existing rolling buffer. The client sends the complete history on its first
call, then only the newest state/observation on later calls. Traffic-light
status, connector id, and timestamp are converted explicitly.

A `Trajectory` contains repeated `EgoState` messages. Each ego state includes
rear-axle pose, rear-axle velocity and acceleration, steering angle, time in
microseconds, angular velocity, and angular acceleration. The converters map
between these messages and nuPlan state objects; they do not repair empty,
non-monotonic, or too-short output. Validate those conditions in the planner
and with the bundled static checker.

## Port and runtime environment

`SubmissionPlanner` reads `SUBMISSION_CONTAINER_PORT` and binds gRPC on
`[::]:<port>`; the effective code default is `50051`. The remote planner uses
localhost and a one-second `ComputeTrajectory` timeout by default, with a
five-second initialization retry window. If a container manager starts the
submission image, it allocates a free host port, passes the port as the
container environment, exposes it, and mounts the data root read-only.

The server reads:

- `NUPLAN_MAP_VERSION`, default `nuplan-maps-v1.0`;
- `NUPLAN_DATA_ROOT`, used to locate the `maps` directory;
- `SUBMISSION_CONTAINER_PORT`.

The Compose setup additionally expects host values for `NUPLAN_DATA_ROOT`,
`NUPLAN_MAPS_ROOT`, and `NUPLAN_EXP_ROOT`, and mounts maps into the submission
container. Missing maps are a data/runtime problem, not a reason to edit the
protocol.

## Protected files and allowed changes

Do not modify or regenerate:

```text
nuplan/submission/protos/challenge.proto
nuplan/submission/challenge_pb2.py
nuplan/submission/challenge_pb2_grpc.py
nuplan/submission/submission_container.py
nuplan/submission/submission_planner.py
```

The challenge guide says the organizer supplies its version of the protocol
files. Changing field order, message types, generated descriptors, service
names, server setup, or container behavior can make a locally passing image
incompatible remotely. Keep the exact files in the base image and report
checksum drift as a packaging defect.

Allowed changes are the custom planner, its Hydra config, extra dependencies
in `requirements_submission.txt`, assets copied by the submission Dockerfile,
and the marked planner-selection command in `entrypoint_submission.sh`. Keep
credentials out of the image and out of static manifests.

## Container checklist

`Dockerfile.submission` is based on a CUDA runtime image, creates a Python 3.9
Conda environment from `environment_submission.yml`, copies the package,
installs it, sets data/map/experiment defaults, and runs the submission
entrypoint. At this source version `requirements_submission.txt` is empty;
append only explicitly needed compatible dependencies. Before a build, check:

- the target module and Hydra config are included in the build context;
- all extra pip dependencies are declared, compatible with the pinned runtime,
  and not silently fetched at serve time;
- model/checkpoint paths are copied into the image and are readable by the
  entrypoint;
- `NUPLAN_DATA_ROOT`, its `maps` child, `NUPLAN_MAP_VERSION`, and the gRPC
  port are coherent;
- the image starts the server rather than a shell or a one-shot test;
- the planner does not read a hidden test split, use credentials, or require a
  network request during `InitializePlanner` or `ComputeTrajectory`;
- container and protocol files remain protected.

The documented local commands are optional and side-effecting:

```bash
docker build --network host -f Dockerfile.submission . -t <image>:<tag>
docker-compose up --build
```

Compose uses host networking, GPU reservation, map/data/experiment mounts, and
an image selected by `SUBMISSION_IMAGE`. A Docker build or Compose run was not
part of this route's verified static checks; state that limitation.

## EvalAI and result formatting

The competition flow sends a tagged image to a selected phase through the
EvalAI CLI. The documented shape is:

```bash
evalai push <image>:<tag> --phase <phase-name>
```

The phase name and exact command must come from the current competition UI.
Uploading is credentialed and remote; do not perform it in a safe preflight.

The optional leaderboard writer reads `submission_metadata.json`, optional
standard-output/error logs, and challenge parquet results. On a successful
run it emits `submission_status: FINISHED`, a JSON `result` with a
`data_split` entry and accuracy metrics for open-loop, closed-loop
non-reactive, closed-loop reactive challenges, and a combined mean score. On a
failed run it emits `submission_status: FAILED` with stdout/stderr. Missing
logs are tolerated; missing metadata or result columns are not silently
repaired. EvalAI credentials are required only by the network interface and
must never appear in a manifest or runtime example.
