# Real-robot bridge considerations

Use this reference when connecting a served StarVLA policy to robot middleware, controller stacks, or GR00T-compatible bridges. It is for schema and safety planning; it does not authorize direct robot execution.

## Evidence notes

- `examples/realRobots/UnitreeG1_WholeBody/step3_deployment/README.md` and `eval_files/model2unitree_g1_interface.py`: websocket policy client adapter, metadata-derived `unnorm_key`, flat action split into controller groups, and dry-run safety order.
- `examples/realRobots/EgoVLA/README.md`, `examples/realRobots/EgoVLA/eval_files/README.md`, `egovla_g1_policy.py`, `server_egovla_g1.py`: GR00T ZMQ route for an EgoVLA-specific G1 bridge and a specialized 48-dim decode path.
- `examples/realRobots/RoboChallenge_table30v2/eval_files/model2robochallenge_interface.py`: RoboChallenge state/image/action bridge shape and why direct-model scripts are not the preferred current server path.
- `examples/realRobots/Franka/README.md` and eval interfaces: older websocket client examples that still describe `normalized_actions`; useful as action-space examples but stale for current server-side unnormalization.

## Bridge responsibility boundary

A robot bridge should do only these jobs:

1. Acquire fresh camera images and robot state from user-owned hardware or simulator/controller middleware.
2. Convert observations into the served policy's request schema.
3. Send `unnorm_key` when the checkpoint has multiple available statistics keys.
4. Consume already-unnormalized `actions` from the StarVLA server.
5. Split flat actions into controller-specific groups or named GR00T action keys.
6. Enforce safety: clipping, velocity/acceleration limits, stale-action checks, pause, emergency stop, and controller health checks.
7. Publish to the controller stack.

A bridge should **not** reimplement dataset statistics unnormalization for the current StarVLA policy server. If an older bridge parses `normalized_actions`, migrate it to `actions` before trusting behavior.

## Websocket bridge pattern

The websocket bridge pattern is:

```text
StarVLA checkpoint -> StarVLA websocket policy server -> robot adapter -> controller stack -> robot
```

Typical adapter request:

```json
{
  "examples": [
    {
      "image": [{"shape": [224, 224, 3], "dtype": "uint8", "description": "RGB camera view"}],
      "lang": "task prompt",
      "state": {"shape": [1, 78], "dtype": "float32", "description": "optional flat proprioception"}
    }
  ],
  "unnorm_key": "unitree_g1_sonic"
}
```

The Unitree G1 whole-body adapter evidence uses this shape and then splits a 78D action chunk into controller groups:

```text
action[0:64]  -> motion token / SONIC latent
action[64:71] -> left hand command
action[71:78] -> right hand command
```

Treat the split as checkpoint/controller-specific. Always verify the actual training DataConfig, statistics key, and controller contract before real execution.

## GR00T-compatible ZMQ bridge pattern

The GR00T-compatible ZMQ route is appropriate when an existing client already speaks the GR00T PolicyServer endpoint protocol.

```text
GR00T-style client/controller -> ZMQ REQ/REP -> StarVLA GR00T-compatible server -> StarVLA checkpoint
```

Operational rules:

- Use the `server_policy_gr00t_zmq.py` entrypoint for ordinary StarVLA checkpoints whose DataConfig already names the state/action groups expected by the bridge.
- Choose `--unnorm_key` explicitly for multi-key checkpoints.
- Call `get_modality_config()` from the bridge side before sending control traffic. Confirm `state_keys`, `state_key_dims`, `action_keys`, and `action_key_dims` match the bridge profile.
- Named input state groups are flattened in DataConfig order. Named output action groups are split from the unnormalized flat action chunk in DataConfig order.
- Only the custom ndarray codec is implemented in the inspected ZMQ server. Configure the bridge to use that codec or add/test a codec adapter.

For new embodiments, the preferred fix is usually a correct DataConfig and statistics key, not per-bridge protocol hardcoding. If the bridge's state/action names differ from the checkpoint DataConfig, decide whether to rename the client groups, register a compatible DataConfig, or add a small deterministic adapter that is covered by tests.

## Specialized model bridge: EgoVLA G1

The EgoVLA G1 evidence is a specialized ZMQ policy server that reuses the generic `ZmqGr00tPolicyServer` transport but does not use the ordinary StarVLA `PolicyServerWrapper` normalization path. It:

- Receives GR00T-style G1 observations.
- Converts ego-view video and wrist proprioception into an EgoVLA example.
- Runs an EgoVLA framework that predicts a 48D camera-frame action chunk.
- Decodes wrist end-effector poses and MANO hand output to G1 joint target groups.
- Returns named GR00T action groups for a G1 bridge.

Treat this script family as reference-only for most StarVLA checkpoint deployments because it requires license-gated assets and robot/sim-specific kinematics/retargeting. The reusable lesson is the boundary: keep the transport protocol generic, keep robot kinematics/retargeting in an adapter, and expose a modality/action contract before control.

## RoboChallenge and Franka evidence status

Some real-robot examples are useful but should not be copied into a current policy-serving bridge without review:

- RoboChallenge evidence loads a checkpoint directly in the bridge and performs its own state normalization/action unnormalization. It is useful for understanding image/state/action dimensions and endpoint semantics, but it bypasses the current policy server boundary.
- Franka evidence documents single-arm 7D and dual-arm 14D action spaces, camera shape expectations, and `env.step(action)` responsibilities. It also contains stale text that expects `normalized_actions` and client-side unnormalization.

When adapting these examples to current StarVLA serving, keep the robot-side observation/action semantics but replace old response parsing with `response["data"]["actions"]` and rely on server-side unnormalization.

## Real-robot dry-run order

Do not begin on real hardware. Use a staged order like:

1. Validate request JSON and metadata with the bundled helper.
2. Run a local mock client/server or recorded-observation replay.
3. Replay a real recorded LeRobot episode into the adapter without publishing commands.
4. Send actions to a mock controller and inspect grouped action ranges.
5. Use a simulator or third-party controller dry-run.
6. Connect to the real robot with the policy paused and commands blocked.
7. Enable low-speed, limited action groups under operator supervision.
8. Gradually expand action groups only after stale-action, clipping, and emergency-stop behavior are verified.

## Required safety gates

Before a bridge can drive physical hardware, require:

- Emergency stop independent of StarVLA and independent of the bridge process.
- Action clipping per controller group.
- Velocity and acceleration limits.
- Stale action timeout and camera/state freshness checks.
- Policy pause/hold command.
- Controller health/heartbeat check.
- Logging of metadata, `unnorm_key`, action chunk size, state/action group dims, and safety-limit config.
- Operator procedure for reset, recovery, and abort.

If any gate is missing, stay in dry-run, replay, or simulation.

## Bridge schema checklist

For every bridge, record these before use:

- Server protocol: websocket or GR00T ZMQ.
- Codec: websocket msgpack-numpy or GR00T custom ndarray codec.
- Metadata snapshot: `action_chunk_size`, `available_unnorm_keys`, selected `unnorm_key`, `training_obs_image_size`.
- Image views: count, order, resolution, color order, camera timestamps.
- State input: names or flat order, dims, units, normalization expectation, history frame selection.
- Action output: flat dims or named groups, chunk length, units, controller group mapping, clipping limits.
- Response key: must be `actions` for the current StarVLA policy server.
- Fallback behavior: what happens on timeout, missing key, action NaN, or controller rejection.
