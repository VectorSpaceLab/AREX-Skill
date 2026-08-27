# Client contracts

Use this reference when writing or debugging clients for a served StarVLA policy. It covers the websocket client path and the GR00T-compatible ZMQ path.

## Evidence notes

- `deployment/model_server/tools/websocket_policy_client.py`: `WebsocketClientPolicy`, metadata handshake, image contract warnings, proxy clearing, timeout behavior.
- `deployment/model_server/tools/websocket_policy_server.py`: websocket message routing and response format.
- `deployment/model_server/tools/msgpack_numpy.py`: websocket ndarray serialization.
- `deployment/model_server/gr00t_obs_adapter.py`: GR00T observation conversion and named action split.
- `deployment/model_server/tools/zmq_policy_server.py`: ZMQ endpoint protocol and custom ndarray codec.
- `tests/test_gr00t_zmq_compat_server.py`: bridge-like client contract, key order, dim split, state history behavior, and error survival.
- Server-related parts of `tests/test_config_overrides.py`: repeatable `--config_override` and metadata override expectations.

## Websocket client lifecycle

`WebsocketClientPolicy` connects to `ws://<host>:<port>` and immediately receives server metadata. Use `host="127.0.0.1"` for a local client; `0.0.0.0` is a bind address, not a connection target.

Client behavior to account for:

- It removes common proxy environment variables before connecting, which avoids accidental websocket proxy routing.
- It waits for the server for up to 300 seconds by default and then raises a timeout.
- It disables websocket compression and uses unlimited message size.
- It stores metadata and exposes `get_server_metadata()`.
- It logs a train/test consistency reminder once per eval run.
- Before each request it checks image counts and image sizes when `training_obs_image_size` is present in metadata; mismatches are warnings, not automatic fixes.

## Websocket request payload

The payload passed to `predict_action()` should be a dict shaped like:

```json
{
  "examples": [
    {
      "image": [
        {"shape": [224, 224, 3], "dtype": "uint8", "description": "RGB camera view placeholder"}
      ],
      "lang": "pick up the red cup",
      "state": {"shape": [1, 7], "dtype": "float32", "description": "optional flat proprioception placeholder"}
    }
  ],
  "unnorm_key": "new_embodiment"
}
```

The JSON above uses shape descriptors so it can be checked by the bundled helper. In a live client, `image` entries are usually NumPy arrays or PIL-compatible image objects, and `state` is a numeric array.

Required and optional payload rules:

- `examples` must be a non-empty list of dicts.
- Each example should include `image` and `lang` for ordinary VLA inference.
- `image` may be a single image or an explicit list of image views. A list is preferred because camera count and order are part of the training contract.
- Image arrays should be RGB, `uint8`, and shaped `[H, W, 3]`. Match `training_obs_image_size` when metadata provides it.
- `state` is optional only for checkpoints trained without proprioception. If used, its dimension/order must match training data and the checkpoint DataConfig.
- `unnorm_key` belongs at the top level of the payload, not inside an individual example. It is mandatory for multi-key checkpoints without a default.
- Other keyword arguments in the payload are forwarded through `PolicyServerWrapper.predict_action(..., **kwargs)` to the framework's `predict_action` method. Only use framework-supported kwargs.

The websocket server also accepts an envelope form:

```json
{
  "type": "infer",
  "request_id": "request-001",
  "payload": {
    "examples": [{"image": [{"shape": [224, 224, 3], "dtype": "uint8"}], "lang": "open the drawer"}],
    "unnorm_key": "new_embodiment"
  }
}
```

`type` may be `infer` or `predict_action`. `ping` returns an ok response and does not run the model.

## Websocket response payload

Current StarVLA policy server response on success:

```json
{
  "status": "ok",
  "ok": true,
  "type": "inference_result",
  "request_id": "request-001",
  "data": {
    "actions": "array shaped [B, T, action_dim]; already unnormalized"
  }
}
```

Important migration rule: `data.actions` is already unnormalized by the server. Older examples and docs may still show `data.normalized_actions` plus client-side unnormalization. Treat those as stale for the current server architecture and migrate clients to `actions`.

Error response from policy inference has:

```json
{
  "status": "error",
  "ok": false,
  "type": "inference_result",
  "request_id": "request-001",
  "error": {"message": "..."}
}
```

A transport-level exception may also be sent as a traceback string before the server closes the websocket. If the client receives a string response, treat it as a server-side exception.

## Metadata-driven client checks

On connect, inspect metadata before sending real robot or benchmark observations:

- `action_chunk_size`: use this for chunk scheduling. Do not infer it from local config.
- `available_unnorm_keys`: choose the correct statistics key. If multiple keys exist, send `unnorm_key` on each request.
- `default_unnorm_key`: optional default selected by the server.
- `training_obs_image_size`: expected `[H, W]` if known. Resize/crop on the client side; the server only warns and forwards observations.
- `training_data_mix`: useful when tracing dataset/statistics mismatches.
- `action_keys` / `state_keys`: may be absent in multi-key lazy mode. If present, use them as a sanity check; for dim checks prefer GR00T `get_modality_config()` or the DataConfig/statistics path.

## GR00T-compatible ZMQ request contract

For the ZMQ path, clients send endpoint messages:

```json
{
  "endpoint": "get_action",
  "data": {
    "observation": {
      "video": {"ego_view": "uint8 array shaped [1, n_frames, H, W, 3]"},
      "state": {
        "left_arm": "float array shaped [1, n_hist, 7]",
        "right_arm": "float array shaped [1, n_hist, 7]"
      },
      "language": {"annotation.human.task_description": [["pick up the apple"]]}
    },
    "options": null
  }
}
```

Supported endpoints:

- `ping`: returns `{"status": "ok", "message": "Server is running"}`.
- `reset`: calls the policy reset hook.
- `get_modality_config`: returns state/action keys, dims, and the selected `unnorm_key`.
- `get_action`: returns a two-item tuple/list equivalent: `(action_dict, info_dict)`.
- `kill`: asks the server loop to shut down.

Codec rule: the inspected server implements the GR00T custom ndarray codec with `__ndarray_class__` and `as_npy`. Do not use the websocket msgpack-numpy ndarray markers for ZMQ unless the server has been explicitly extended and tested.

## GR00T observation conversion

`Gr00tCompatPolicy` converts GR00T observations into StarVLA examples:

- `video`: must be a non-empty dict. For each view, it takes the latest frame. Supported shapes include `[1, n_frames, H, W, 3]`, `[n_frames, H, W, 3]`, or `[H, W, 3]`.
- `state`: required when the checkpoint has state keys and `--no_state` was not used. Incoming subkeys must match checkpoint `state_keys` after removing the `state.` prefix.
- State arrays must have the expected last dimension for each key. The latest history frame is selected, then all state groups are concatenated in DataConfig order.
- Language is read from `language["annotation.human.task_description"]`; if absent, the adapter uses the fallback instruction.

## GR00T action response

`get_action` returns named action groups using checkpoint `action_keys` and `action_key_dims`:

```text
{
  "left_arm":  float32 array [1, T, 7],
  "right_arm": float32 array [1, T, 7],
  ...
},
{"unnorm_key": "...", "action_dim": D}
```

Bridge clients commonly consume `actions[key][0]`, giving `[T, dim]`. If a key is missing or a dim is wrong, compare the client's bridge profile with `get_modality_config()` and the checkpoint DataConfig.

## Helper workflow

The bundled helper does not load checkpoints or open network sockets. Use it to validate JSON-shaped requests and metadata before trying a live server:

```text
scripts/check_policy_server_contract.py --print-examples
scripts/check_policy_server_contract.py --request-json request.json --metadata-json metadata.json
scripts/check_policy_server_contract.py --check-zmq-codec
```

The helper accepts shape descriptors like `{"shape": [224, 224, 3], "dtype": "uint8"}` so you can validate contracts without embedding image arrays in JSON.
