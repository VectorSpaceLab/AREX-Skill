# Runtime architecture

Read this when a request crosses multiple AlpaSim services, when event ordering
is unclear, or when a log shows a failure after startup.

## Responsibilities and direction

The runtime is the central client and state owner. It keeps the simulated world
state, schedules timestamped events, sends gRPC requests, and broadcasts log
entries. The other services are server endpoints; they do not call each other
through the runtime's orchestration path.

A normal closed-loop step follows this conceptual order:

1. Render camera observations for the current/next timestamps.
2. Update the driver's egomotion history, route, and optional recorded ground
   truth; wait for the observation barrier.
3. Ask the driver for a trajectory over the next control interval.
4. Send the trajectory to the controller/vehicle model.
5. Apply physics ground correction to ego and, when enabled, traffic actors.
6. Advance the traffic simulation.
7. Commit/log the resulting state and schedule the next recurring events.

The event queue is a priority queue ordered by simulation timestamp and an
explicit priority for same-timestamp events. Events are self-scheduling, so
camera cadence, pose reporting cadence, and policy cadence can differ. The
policy event must not call the driver until all observations for that decision
are available.

## Service roles

| Runtime handle | Role | Session behavior |
| --- | --- | --- |
| `renderer` | Produces camera frames; sensorsim is per-frame, video-model is stateful | Opens a rollout session; video-model sends static conditioning and closes a remote session |
| `driver` | Consumes images, egomotion, route, and optional GT; returns planned trajectory | Opens a policy session and receives observations for each decision |
| `controller` | Converts planned trajectory to vehicle/egomotion response | Opens a rollout session |
| `physics` | Applies ground constraints to ego/traffic poses | Opens a rollout session when enabled |
| `trafficsim` | Advances non-ego actors and traffic session state | Opens a per-rollout session |
| `runtime` | Coordinates, logs, evaluates, and manages workers | One-shot client or daemon server |

All service wrappers share a lifecycle context. Entering a rollout session opens
the gRPC channel, records the UUID and typed session configuration, and invokes
service initialization. Exiting always attempts cleanup and channel close,
even when initialization or event handling raised an exception. Calling a
session-dependent method outside that context is a lifecycle error, not a
transient network failure.

## Rollout state and timing anchors

A rollout is prepared before the event loop starts. The runtime derives an
execution timeline from the scene's recorded egomotion, camera frame ranges,
force-GT duration, control cadence, and optional start offset. Important
anchors are:

- `render_start_timestamp_us`: first camera-render anchor;
- `first_policy_timestamp_us`: first policy/control pipeline timestamp;
- `closed_loop_start_us`: force-GT to policy handover boundary;
- `end_timestamp_us`: simulation end;
- `control_timestep_us`: recurring policy/controller/physics/traffic period.

The event loop seeds recorded context before the first policy decision. If
physics correction is enabled during force-GT, the runtime can blend the
recorded trajectory with physics-corrected trajectory before closed-loop
control. `planner_delay_us` is represented with a delay buffer rather than by
silently changing service cadence.

## Worker and dispatch model

The parent process builds version IDs once, validates scenarios, loads scene
metadata, and assigns concrete endpoints. A worker receives an assigned job,
constructs lightweight service clients, creates the rollout, and returns a
`JobResult` containing success/error, rollout UUID, and optional in-runtime
metrics. Workers do not independently decide service addresses or versions.

For one worker, the loop runs inline and is convenient for breakpoints. For
multiple workers, child processes use spawn semantics. The daemon scheduler
acquires one slot from every required service pool before dispatching a job;
failed acquisition releases reserved slots. A retryable failure may be queued
again up to `max_rollout_retries`; invalid-scene failures are treated as
deterministic and are not retried.

## Outputs and causal reading

A successful rollout writes an ASL log and marks its rollout directory with
`_complete`. Evaluation and aggregate outputs are downstream products; read
the evaluation route for their meaning. Runtime debugging should correlate:

- `rollout.asl` for message chronology and replay;
- resolved user/network configs for the exact runtime inputs;
- service text logs for startup and RPC errors;
- scheduler/telemetry logs for queue depth, capacity, and worker crashes.

Do not infer a service implementation detail from a metric alone. Start at the
first startup, version, scene, or event-loop error and then inspect the owning
service route when the failure is not runtime orchestration.
