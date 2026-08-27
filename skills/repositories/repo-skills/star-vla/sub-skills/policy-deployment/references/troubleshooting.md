# Policy deployment troubleshooting

Use this guide for StarVLA policy-server/client failures before reopening repository source. For data registry/statistics construction, route to `../data-integration/SKILL.md`. For simulator stacks, route to `../benchmark-evaluation/SKILL.md`. For training or checkpoint creation, route to `../training-config/SKILL.md`.

## Fast triage order

1. Confirm server protocol: websocket or GR00T ZMQ.
2. Capture server metadata or `get_modality_config()`.
3. Verify selected `unnorm_key` against `available_unnorm_keys`.
4. Validate request image/state shapes with `scripts/check_policy_server_contract.py`.
5. Confirm the client expects `actions`, not `normalized_actions`.
6. Check port, host, timeout, and codec.
7. Only then investigate model quality, controller behavior, or robot/simulator environment problems.

## Missing checkpoint config or statistics

Symptoms:

- Server fails during `PolicyServerWrapper` or `PolicyNormProcessor` construction.
- Errors mention missing `datasets.vla_data.data_mix`, `dataset_statistics.json`, unavailable `DATASET_NAMED_MIXTURES`, or unavailable `ROBOT_TYPE_CONFIG_MAP`.

Likely causes and fixes:

- The checkpoint path does not follow the expected run layout with config/statistics near the checkpoint. Serve the training run checkpoint, not a copied weight file without its metadata.
- The training data registry for the checkpoint's `data_mix` is not importable. Route to `../data-integration/SKILL.md` to confirm registry discovery and DataConfig names.
- The checkpoint was trained before current normalization metadata conventions. Either recover the matching statistics/config or create a compatibility adapter and verify it with a synthetic request.

## Multiple unnormalization keys

Symptoms:

- Metadata lists multiple `available_unnorm_keys` and `default_unnorm_key` is null.
- Inference fails with a message like `unnorm_key not specified` or `Multiple unnorm_keys`.

Fix:

- Choose the embodiment/statistics key for the current client.
- For websocket payloads, include top-level `unnorm_key` on every inference request.
- For GR00T ZMQ serving, start the server with `--unnorm_key` or ensure the wrapper default is unambiguous.
- If the correct key is unclear, inspect the checkpoint `training_data_mix`, DataConfig, and dataset statistics through the data-integration route.

## Wrong request image shape or camera contract

Symptoms:

- Client logs a train/test consistency warning.
- Silent performance drop without a shape exception.
- Server receives the request but results are nonsensical.

Checks:

- Each image should be RGB, `uint8`, and shaped `[H, W, 3]`.
- If metadata has `training_obs_image_size`, resize/crop explicitly to that `[H, W]` before sending.
- Camera count and order must match training. The server does not infer, reorder, or auto-select views.
- For GR00T observations, video entries may include history, but the adapter uses only the latest frame.

Use the bundled helper with a JSON shape descriptor to catch obvious mistakes before live traffic.

## Wrong state shape, state keys, or dims

Symptoms:

- GR00T ZMQ returns `{"error": "... missing ..."}`.
- Errors mention a state key's expected last dim.
- Websocket request works but policy behavior is poor.

Fixes:

- For websocket clients, send state only if the checkpoint was trained with state. Its flat order and dimension must match training.
- For GR00T clients, call `get_modality_config()` and compare bridge state names/dims against `state_keys` and `state_key_dims`.
- Incoming GR00T state keys are subkeys like `left_arm`; the adapter matches them to checkpoint keys like `state.left_arm`.
- GR00T state history is reduced to the latest frame. If a controller expects temporal stacking, implement and test that explicitly instead of assuming the adapter does it.

## Client expects `normalized_actions`

Symptoms:

- KeyError on `response["data"]["normalized_actions"]`.
- Client unnormalizes an already-unnormalized `actions` chunk and sends invalid robot commands.
- Real-robot examples mention client-side statistics despite current server metadata.

Fix:

- Current StarVLA policy server returns `response["data"]["actions"]`.
- Remove local `read_mode_config`, local action-stat lookup, and hand-written unnormalization from policy clients unless you are intentionally bypassing the server wrapper.
- Use metadata `action_chunk_size` for chunk scheduling.
- Treat older Franka/RoboChallenge-style normalized-action docs as reference-only until migrated.

## ZMQ codec mismatch

Symptoms:

- ZMQ request times out or server errors while unpacking.
- Arrays arrive as dicts rather than NumPy arrays.
- Bridge configured for an alternate GR00T serialization mode.

Fix:

- The inspected StarVLA ZMQ server implements the custom GR00T ndarray codec: `{"__ndarray_class__": true, "as_npy": <np.save bytes>}`.
- Do not use the websocket msgpack-numpy markers (`__ndarray__`, raw bytes/dtype/shape) for ZMQ traffic.
- If a bridge uses a different GR00T codec, switch it to custom mode or add a tested codec adapter.
- Run `scripts/check_policy_server_contract.py --check-zmq-codec` to verify local pack/unpack dependencies and codec roundtrip.

## Port conflicts, bind/connection mistakes, and timeouts

Symptoms:

- Server fails to start with address already in use.
- Client waits until timeout.
- Client tries to connect to `0.0.0.0`.

Fixes:

- Pick a free port and keep websocket and ZMQ ports distinct.
- Servers bind to `0.0.0.0`; local clients should connect to `127.0.0.1` or the actual host address.
- Websocket client waits for up to 300 seconds by default. If it times out, confirm the server started and sent metadata.
- ZMQ REQ/REP clients require one reply per request. The inspected server catches handler exceptions and replies with `{"error": ...}` to keep the loop alive.
- Check firewall/container networking if client and server are in different environments.

## `use_bf16` and device mistakes

Symptoms:

- Server fails while moving model to device or casting to bfloat16.
- CPU-only debug attempts fail unexpectedly.
- CUDA device is unavailable or out of memory.

Fixes:

- Use `--use_bf16` only on hardware and model paths that support bfloat16 inference.
- The inspected websocket and ZMQ entrypoints construct `PolicyServerWrapper` with device `cuda`. For CPU-only smoke tests, use mocks or a small custom wrapper rather than expecting those entrypoints to load real checkpoints on CPU unchanged.
- Confirm the intended accelerator is visible to the serving process and that checkpoint/model dependencies are installed.
- If a checkpoint needs a compatibility override, use the websocket `--config_override KEY=VALUE` path; the inspected ZMQ entrypoint does not expose `--config_override`.

## Config override syntax failures

Symptoms:

- Errors mention `Expected KEY=VALUE`.
- A boolean override remains a string or has no effect.
- Python API rejects `config_overrides` as a bare string.

Fixes:

- Pass repeatable dotlist entries: one `KEY=VALUE` per override.
- Later duplicate entries override earlier entries.
- Use a list/tuple of dotlist strings in Python code.
- Avoid logging sensitive override values; the inspected server logs only override keys.

## Action chunk size mismatch

Symptoms:

- Client requests a new action chunk too frequently or too slowly.
- Controller consumes the wrong number of planned actions.

Fix:

- Read `action_chunk_size` from server metadata.
- Do not infer chunk size from local YAML, old client helpers, or action dimension.
- For GR00T named-action clients, also check `get_modality_config()` action dims; chunk length is the time dimension, not the sum of action dims.

## Real-robot bridge safety failures

Symptoms:

- Adapter can send commands but lacks clipping, heartbeat, stale-action timeout, or emergency stop.
- Action groups or units have not been verified against the controller.

Fix:

- Stop at dry-run or simulation.
- Add group-wise safety limits and controller health checks.
- Log metadata, selected `unnorm_key`, action dims, and safety configuration.
- Rehearse operator abort and pause procedures before enabling motion.
