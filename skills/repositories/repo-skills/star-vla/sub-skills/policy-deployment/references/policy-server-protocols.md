# Policy server protocols

This reference captures the StarVLA policy-serving contracts that a future agent should use without reopening the source repository. Evidence notes are relative source paths from the inspected StarVLA checkout; they are not runtime links or dependencies.

## Evidence notes

- `deployment/model_server/README.md`, `deployment/readme-deployment.md`: public serving guidance, GR00T ZMQ addition, and the 2025-05 server-side unnormalization migration.
- `deployment/model_server/policy_wrapper.py`: `PolicyServerWrapper`, metadata, lazy multi-key unnormalization, config override plumbing.
- `deployment/model_server/policy_norm_processor.py`: training-time transform reconstruction and per-key action/state dims.
- `deployment/model_server/server_policy.py`: websocket entrypoint and repeatable `--config_override` parser.
- `deployment/model_server/server_policy_gr00t_zmq.py`, `deployment/model_server/gr00t_obs_adapter.py`, `deployment/model_server/tools/zmq_policy_server.py`: GR00T-compatible ZMQ protocol, named state/action adapter, custom ndarray codec.
- `deployment/model_server/tools/websocket_policy_server.py`, `deployment/model_server/tools/websocket_policy_client.py`, `deployment/model_server/tools/msgpack_numpy.py`: websocket handshake, request routing, and msgpack-numpy transport.
- `tests/test_gr00t_zmq_compat_server.py`, server-related parts of `tests/test_config_overrides.py`: test-backed protocol and override behavior.

## Component roles

### `PolicyServerWrapper`

`PolicyServerWrapper` is the serving façade around a loaded `baseframework` checkpoint.

- Loads the checkpoint with `baseframework.from_pretrained(ckpt_path, config_overrides=config_overrides)`.
- Moves the framework to the requested device and optionally casts to bfloat16.
- Reads co-located checkpoint config/statistics and applies the same config overrides to metadata resolution.
- Computes `action_chunk_size` from either:
  - `framework.action_model.action_horizon`, or
  - `framework.action_model.future_action_window_size + 1` for older LIBERO-style configs.
- Peeks at `dataset_statistics.json` top-level keys as `available_unnorm_keys`.
- Uses eager normalization processor construction only when a default `unnorm_key` is explicit or exactly one statistics key exists.
- Enters **multi-key lazy mode** when multiple statistics keys exist and no default key is supplied. In that mode, each inference request must include `unnorm_key`.
- Calls the underlying framework, reads its `normalized_actions`, applies `PolicyNormProcessor.unapply_actions`, and returns `{"actions": unnormalized_array}`.

### `PolicyNormProcessor`

`PolicyNormProcessor` is the single source of action unnormalization for the policy server.

- Resolves the training `data_mix` from checkpoint config.
- Looks up the mixture in `DATASET_NAMED_MIXTURES` and chooses the `robot_type`; multi-robot mixtures require an explicit `unnorm_key` that matches a robot type/statistics key.
- Finds the corresponding `DataConfig` in `ROBOT_TYPE_CONFIG_MAP`.
- Rebuilds the training-time transform pipeline and binds reconstructed `DatasetMetadata`.
- Splits combined `dataset_statistics.json` arrays into per-key entries using explicit `action_key_dims` / `state_key_dims` when present; otherwise it infers uniform dims only when safe.
- Exposes `action_keys`, `state_keys`, `action_key_dims`, `state_key_dims`, `unnorm_key`, and `available_unnorm_keys` for adapters.
- `unapply_actions(normalized_actions)` expects `(T, D)` and returns `(T, D)` with dims ordered according to `action_keys`.

### Websocket server (`server_policy.py` + `WebsocketPolicyServer`)

The websocket server is the standard StarVLA policy-serving path.

Entrypoint arguments from the inspected parser:

- `--ckpt_path`: checkpoint path.
- `--port`: websocket port, default `10093`.
- `--use_bf16`: cast the loaded framework to bfloat16 before serving.
- `--idle_timeout`: idle shutdown in seconds; `-1` disables auto-close.
- `--config_override KEY=VALUE`: repeatable OmegaConf dotlist override applied before model construction and metadata resolution.

Protocol behavior:

1. The server constructs `PolicyServerWrapper` and starts `WebsocketPolicyServer` on host `0.0.0.0`.
2. On connection, the server sends metadata as a msgpack-numpy blob.
3. Each subsequent client message is unpacked and routed.
4. Supported message styles:
   - Envelope: `{"type": "infer", "request_id": "...", "payload": {...}}`.
   - Flat payload: `{...}`; treated as an inference payload.
   - `type` may be `infer` or `predict_action`; `ping` is also supported.
5. Inference calls `policy.predict_action(**payload)`.
6. Success response: `{"status": "ok", "ok": true, "type": "inference_result", "request_id": ..., "data": {"actions": ...}}`.
7. Policy exceptions are encoded as `{"status": "error", "ok": false, "error": {"message": ...}}` instead of silently wedging the connection.

The websocket msgpack codec uses ndarray markers named `__ndarray__`, with raw bytes, dtype, and shape. It is distinct from the GR00T ZMQ custom codec below.

## Server metadata contract

Use metadata as the first compatibility check before debugging model quality. Important fields from `PolicyServerWrapper.metadata`:

| Field | Meaning |
| --- | --- |
| `env` | Serving environment tag; inspected code uses `starvla_policy_server`. |
| `ckpt_path` | The served checkpoint identifier/path as seen by the server. Treat it as informational; do not require clients to know the server filesystem. |
| `action_chunk_size` | Number of actions returned per inference chunk. Clients should schedule chunk reuse from this field rather than recomputing from config. |
| `available_unnorm_keys` | Top-level keys available in checkpoint statistics. If more than one key and `default_unnorm_key` is null, requests must include `unnorm_key`. |
| `default_unnorm_key` | Default statistics key if one was chosen at server startup. |
| `training_data_mix` | Data mixture from the resolved checkpoint config, after config overrides. |
| `training_obs_image_size` | Expected training image size `[H, W]` when explicitly available. Null means no strict value was recovered. |
| `eval_image_contract` | Reminder that the server does not infer camera count or order. |
| `action_keys`, `state_keys` | Present when a default normalization processor is already built. For multi-key lazy mode these may be absent until an `unnorm_key` selects an embodiment. |

The GR00T adapter also exposes `get_modality_config()`, which includes `action_key_dims` and `state_key_dims`; use that endpoint for named state/action handshakes.

## Config override behavior

Use repeatable dotlist entries:

```text
--config_override framework.action_model.diffusion_model_cfg.use_canonical_forward=false
--config_override framework.action_model.diffusion_model_cfg.num_inference_timesteps=6
```

Test-backed behavior:

- `KEY=VALUE` entries are parsed by OmegaConf, so `false` becomes boolean false and numeric values become numbers when possible.
- Later duplicate overrides win.
- Invalid entries without `=` raise a clear `Expected KEY=VALUE` error.
- Passing a bare string as the Python `config_overrides` argument is rejected; pass a list or tuple of strings.
- `server_policy.py` logs override keys, not full values, to reduce accidental secret exposure.

Observed limitation: the inspected GR00T ZMQ entrypoint exposes `--unnorm_key` but not `--config_override`. If a ZMQ deployment needs a checkpoint compatibility override, either serve through websocket plus a bridge adapter, or extend the ZMQ entrypoint intentionally and verify the override path.

## GR00T-compatible ZMQ server

`server_policy_gr00t_zmq.py` serves the same checkpoint over a ZMQ REQ/REP protocol compatible with Isaac-GR00T N1.6 custom serialization and GR00T-WBC-Bridge-style clients.

Entrypoint arguments from the inspected parser:

- `--ckpt_path`: required checkpoint path.
- `--host`: bind host, default `0.0.0.0`.
- `--port`: ZMQ port, default `5555`.
- `--use_bf16`: cast the loaded framework to bfloat16.
- `--unnorm_key`: statistics key; required for multi-dataset/multi-robot checkpoints.
- `--no_state`: do not forward proprioceptive state into StarVLA examples.
- `--fallback_instruction`: language instruction used when the observation has none.

Transport and endpoints:

- Transport is ZMQ REQ/REP: one msgpack blob per request and response.
- Request shape is `{"endpoint": endpoint_name, "data": {...}}`; endpoint defaults to `get_action`.
- Endpoints: `ping`, `kill`, `get_action`, `reset`, `get_modality_config`.
- Errors are returned as `{"error": "..."}` and the server loop should keep answering later requests.
- The custom ndarray codec encodes arrays as `{"__ndarray_class__": true, "as_npy": <np.save bytes>}`.
- Only the N1.6-style custom codec is implemented in the inspected server. Do not assume compatibility with the alternate msgpack-numpy codec unless you add and test it.

## GR00T observation/action adapter

`Gr00tCompatPolicy` presents `PolicyServerWrapper` as a GR00T policy object.

Input observation contract:

```text
{
  "video": {"<view>": uint8 array shaped (1, n_frames, H, W, 3) or compatible},
  "state": {"<state_subkey>": float array shaped (1, n_hist, dim) or compatible},
  "language": {"annotation.human.task_description": [["instruction"]]}
}
```

Conversion rules:

- For each video entry, the adapter takes the latest frame and builds StarVLA `example["image"]` as a list of images in the received view order.
- For state, it iterates checkpoint `state_keys`, strips the modality prefix, requires each subkey in the incoming state dict, takes the latest history frame, and concatenates values into one flat state vector.
- If `--no_state` is used or the checkpoint has no state keys, state is not forwarded.
- Language is read from `annotation.human.task_description`; a fallback instruction is used if absent.
- The wrapper returns flat unnormalized actions shaped `(B, T, D)`.
- `split_actions` uses checkpoint `action_keys` and `action_key_dims` to return named action arrays shaped `(B, T, dim_k)`.
- `get_modality_config()` returns a plain dict with `state_keys`, `state_key_dims`, `action_keys`, `action_key_dims`, and `unnorm_key` for bridge-side verification.
