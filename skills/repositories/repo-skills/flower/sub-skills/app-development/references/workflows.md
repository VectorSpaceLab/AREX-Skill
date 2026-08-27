# Workflows

## 1) Typical authoring loop
1. Scaffold or pull the app with `flwr new`.
2. Edit `pyproject.toml` so Flower can find your `ServerApp` and `ClientApp`.
3. Implement the server-side entry point with `ServerApp`.
4. Implement client-side handlers with `ClientApp`.
5. Validate the app wiring with `scripts/check_flower_app.py`.
6. Run locally with `flwr run . local --stream` or remotely with SuperGrid.
7. Iterate on logs, `Context.run_config`, and message payloads.

## 2) Minimal `ServerApp`
Use `ServerApp()` plus `@app.main()` as the default app entry style.

```python
from flwr.app import ArrayRecord, ConfigRecord, Context
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg

app = ServerApp()


@app.main()
def main(grid: Grid, context: Context) -> None:
    num_rounds = int(context.run_config["num-server-rounds"])
    model_state = ...  # list of ndarrays or a state_dict
    arrays = ArrayRecord(model_state)
    strategy = FedAvg()
    result = strategy.start(
        grid=grid,
        initial_arrays=arrays,
        num_rounds=num_rounds,
        train_config=ConfigRecord({"lr": 0.1}),
    )
```

## 3) Minimal `ClientApp`
Use `ClientApp()` plus `@app.train()` / `@app.evaluate()` / `@app.query()`.

```python
from flwr.app import ArrayRecord, ConfigRecord, Context, Message, MetricRecord, RecordDict
from flwr.clientapp import ClientApp

app = ClientApp()


@app.train()
def train(msg: Message, context: Context) -> Message:
    arrays = msg.content.array_records["arrays"].to_numpy_ndarrays()
    lr = float(msg.content.config_records["config"]["lr"])
    updated = [arr + lr for arr in arrays]
    return Message(
        RecordDict({
            "arrays": ArrayRecord(updated),
            "metrics": MetricRecord({"loss": 0.1, "num-examples": 2}),
        }),
        reply_to=msg,
    )
```

## 4) pyproject wiring
A Flower App needs its own `pyproject.toml` with the app metadata and component paths.

```toml
[project]
name = "your-flower-app"
version = "1.0.0"
dependencies = ["flwr>=1.34.0"]

[tool.flwr.app]
publisher = "your-name-or-organization"

[tool.flwr.app.components]
serverapp = "your_package.server_app:app"
clientapp = "your_package.client_app:app"

[tool.flwr.app.config]
num-server-rounds = 3
learning-rate = 0.1
```

Tips:
- Use kebab-case keys in `[tool.flwr.app.config]` and read them from `context.run_config`.
- If you need to bundle only part of the tree, add `fab-include` / `fab-exclude` carefully.
- Some repo examples also add `fab-format-version` and `flwr-version-target` for bundle-compatibility metadata.

## 5) Run/debug loop
- Local debug: `flwr run . local --stream`
- SuperGrid flow: `flwr login supergrid`, then `flwr run . supergrid`
- Override config values at runtime with `--run-config`
- Use `flwr new @publisher/app` when you want a known-good app scaffold to edit

## 6) Stateful clients
`ClientApp` objects are recreated for each message. Keep app objects stateless and store
run-scoped state in `context.state`.

Typical pattern:

```python
from flwr.app import Context, Message, MetricRecord, RecordDict

@app.train()
def train(msg: Message, context: Context) -> Message:
    if "history" not in context.state.metric_records:
        context.state.metric_records["history"] = MetricRecord({"count": 0})
    context.state.metric_records["history"]["count"] += 1
    return Message(RecordDict(), reply_to=msg)
```

Use `context.node_config` for per-node values such as `partition-id` or `num-partitions`,
and use `context.run_config` for per-run settings such as batch size or round count.

## 7) Compatibility patterns
- Prefer `ServerApp()` + `@app.main()` for new apps.
- Keep `server_fn` only for legacy compatibility cases.
- Prefer `ClientApp()` + message-type decorators for new apps.
- Keep `client_fn(context)` only when you are bridging older client code.
- If you need setup/cleanup around the app, add a `lifespan()` generator.
