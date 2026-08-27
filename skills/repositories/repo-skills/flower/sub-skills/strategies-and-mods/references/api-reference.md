# Strategies and mods API reference

Read this when you need the verified Flower strategy surface, aggregation
parameters, or `ClientApp` mod behavior.

## Verified strategy surface

The inspected package exports these strategy classes from
`flwr.serverapp.strategy`:

- `Strategy`
- `FedAvg`
- `FedAdam`
- `FedAdagrad`
- `FedProx`
- `FedAvgM`
- `FedYogi`
- `FedMedian`
- `FedTrimmedAvg`
- `Krum`
- `MultiKrum`
- `Bulyan`
- `QFedAvg`
- `FedXgbBagging`
- `FedXgbCyclic`
- differential-privacy wrappers for client-side and server-side clipping

## Verified signatures

```python
Strategy.start(grid, initial_arrays, num_rounds=3, timeout=3600, train_config=None, evaluate_config=None, evaluate_fn=None)
Strategy.configure_train(server_round, arrays, config, grid)
Strategy.configure_evaluate(server_round, arrays, config, grid)
Strategy.aggregate_train(server_round, replies)
```

Common constructor parameters on the built-ins include:

- `fraction_train`
- `fraction_evaluate`
- `min_train_nodes`
- `min_evaluate_nodes`
- `min_available_nodes`
- `weighted_by_key`
- `arrayrecord_key`
- `configrecord_key`
- strategy-specific optimizer or robust-aggregation parameters

Examples from the inspected environment:

```python
FedAvg(..., train_metrics_aggr_fn=None, evaluate_metrics_aggr_fn=None)
FedAdam(..., eta=0.1, eta_l=0.1, beta_1=0.9, beta_2=0.99, tau=0.001)
FedAdagrad(..., eta=0.1, eta_l=0.1, tau=0.001)
FedProx(..., proximal_mu=0.0)
```

## Verified mod surface

The mod type used by `ClientApp` is:

```python
Callable[[Message, Context, ClientAppCallable], Message]
```

The mod system supports:

- application-wide mods passed to `ClientApp(mods=[...])`
- function-specific mods attached to `@app.train(mods=[...])` or similar
- ordering that wraps application-wide mods outside function-specific mods

## Common design patterns

- Use `weighted_by_key="num-examples"` unless the message payload uses a
  different metric name for weighting.
- Use `train_config` and `evaluate_config` when a per-round config should be sent
  to the clients.
- Override `configure_train` or `configure_evaluate` when the config itself must
  change from round to round.
- Override `summary()` or use it when you want a concise log of strategy
  parameters during debugging.

## Where to go next

- Read [workflows.md](workflows.md) for strategy selection and customization.
- Read [troubleshooting.md](troubleshooting.md) for skipped rounds, mod-order
  confusion, and aggregation-key mistakes.
