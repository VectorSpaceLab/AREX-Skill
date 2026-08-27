# API reference

This page summarizes the verified Flower app-facing API for authoring and wiring a
Flower App.

## Public import map
- `flwr.app`: `Array`, `ArrayRecord`, `ConfigRecord`, `Context`, `Message`,
  `MetricRecord`, `RecordDict`, plus `DEFAULT_TTL`, `MessageType`, `Metadata`, and
  `Error`
- `flwr.clientapp`: `ClientApp`
- `flwr.serverapp`: `Grid`, `ServerApp`, `strategy`
- `flwr.serverapp.strategy`: `Strategy` and built-ins such as `FedAvg`, `FedAdam`,
  `FedProx`, `FedAvgM`, `FedYogi`, `FedMedian`, `FedTrimmedAvg`, `Krum`, `MultiKrum`,
  and `Bulyan`

Implementation homes in the framework tree mirror those public imports:
`flwr.app.message` for the core value objects, `flwr.clientapp.client_app` for
`ClientApp`, and `flwr.serverapp.server_app` for `ServerApp`.

## Core value objects

| Symbol | Verified signature or forms | Notes |
| --- | --- | --- |
| `Array` | `Array(dtype, shape, stype, data)`; `Array(ndarray)`; `Array(torch_tensor)` | Serialized array/tensor wrapper. |
| `ArrayRecord` | `ArrayRecord()`; `ArrayRecord(array_dict, keep_input=True)`; `ArrayRecord(numpy_ndarrays, keep_input=True)`; `ArrayRecord(torch_state_dict, keep_input=True)` | Use `to_numpy_ndarrays()` and `to_torch_state_dict()` to unwrap. |
| `ConfigRecord` | `ConfigRecord(config_dict=None, keep_input=True)` | Values may be `bool`, `int`, `float`, `str`, `bytes`, or homogeneous lists of those. |
| `MetricRecord` | `MetricRecord(metric_dict=None, keep_input=True)` | Values may be `int`, `float`, or homogeneous lists of those. `bool` is not allowed. |
| `RecordDict` | `RecordDict(records=None, *, parameters_records=None, metrics_records=None, configs_records=None)` | Only `ArrayRecord`, `MetricRecord`, and `ConfigRecord` are accepted. The `*_records` constructor args and `parameters_records` / `metrics_records` / `configs_records` views are deprecated aliases. |
| `Message` | `Message(content, dst_node_id, message_type, *, ttl=None, group_id=None, dst_task_id=None)`; `Message(content, *, reply_to, ttl=None)`; `Message(error, *, reply_to, ttl=None)` | `content` and `error` are mutually exclusive. Replies inherit routing metadata from `reply_to`. |
| `Context` | `Context(run_id, node_id, node_config, state, run_config, series_id=0)` | `state` and `run_config` are run-scoped; `node_config` persists on the node. |

## App entry points

### ClientApp
- Constructor: `ClientApp(client_fn=None, mods=None)`
- Preferred handlers: `@app.train()`, `@app.evaluate()`, `@app.query()`
- Optional `mods` can wrap the whole app or a single handler.
- Route names follow `train`, `evaluate`, `query`, or `category.action`, where
  `action` must be a valid Python identifier.
- `@app.lifespan()` registers a setup/teardown generator that must yield exactly once.

### ServerApp
- Constructor: `ServerApp(server=None, config=None, strategy=None, client_manager=None, server_fn=None)`
- Preferred handler: `@app.main()` with `main(grid: Grid, context: Context) -> None`
- `@app.lifespan()` works the same way as on `ClientApp`
- `Grid` is the server-side transport abstraction passed into `main`
- New-style apps usually call `strategy.start(grid=..., initial_arrays=..., num_rounds=..., train_config=..., evaluate_config=..., evaluate_fn=...)`
- `server_fn` is the legacy compatibility path that returns `ServerAppComponents`

## pyproject wiring
- `[tool.flwr.app].publisher` names the app publisher.
- `[tool.flwr.app].components.serverapp` and `.clientapp` must be `<module>:<object>`
  references to the app entry points.
- `[tool.flwr.app].config` holds run-time defaults that become `context.run_config`.
- `fab-include` and `fab-exclude` are optional packaging filters.
- Some templates also include `fab-format-version` and `flwr-version-target` for FAB
  compatibility metadata.

## Route decisions
- `ClientApp` without `client_fn` dispatches by `Message.message_type`.
- `client_fn` is the legacy compatibility path and should now accept `def client_fn(context: Context)`.
- `ClientApp(client_fn=...)` and `@app.train()` / `@app.evaluate()` / `@app.query()` are mutually exclusive.
- `ServerApp` prefers the new `@app.main()` style. If you pass deprecated direct constructor args (`server`, `config`, `strategy`, `client_manager`) and then register `main`, Flower raises a `ValueError`.
- Use `Context.run_config` for run-level settings and `Context.node_config` for node-specific settings.

## Lifecycle notes
- `ClientApp` and `ServerApp` each support a `lifespan()` decorator.
- The decorated function receives `Context`, must be a generator, and must yield once.
- No yield or multiple yields raises a runtime error.
- Use lifespan for setup and cleanup around a run, not for per-message state.

## Record semantics
- `Message.content` and `Context.state` should use `RecordDict`.
- `RecordDict.array_records`, `RecordDict.metric_records`, and `RecordDict.config_records` are synchronized typed views.
- Use `ArrayRecord` for arrays or model parameters, `MetricRecord` for scalar metrics, and `ConfigRecord` for runtime configuration values.
- For model state, `ArrayRecord` can round-trip NumPy ndarrays or PyTorch `state_dict`s.

## Compatibility notes
- `Message.create_reply` and `Message.create_error_reply` are deprecated; construct replies with `Message(..., reply_to=...)`.
- `RecordDict.parameters_records`, `metrics_records`, and `configs_records` are deprecated aliases.
- Legacy `client_fn(cid)` still adapts with a warning, but the preferred signature is `client_fn(context: Context)`.
- If a legacy `client_fn` returns `NumPyClient`, Flower converts it to `Client` and warns; prefer `NumPyClient.to_client()`.
- Import `Context` from `flwr.app` and `ServerApp` from `flwr.serverapp`; older import locations are deprecated.
