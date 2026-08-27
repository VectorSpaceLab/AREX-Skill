# Strategies and mods workflows

## 1. Choose a built-in strategy

Start from the workflow goal:

- **Plain federated averaging** → `FedAvg`
- **Adaptive optimization-like updates** → `FedAdam`, `FedAdagrad`, `FedYogi`
- **Proximal or personalized updates** → `FedProx`, `FedAvgM`, `QFedAvg`
- **Robust aggregation** → `FedMedian`, `FedTrimmedAvg`, `Krum`, `MultiKrum`, `Bulyan`
- **XGBoost federation** → `FedXgbBagging`, `FedXgbCyclic`
- **Privacy wrapper** → the DP wrappers around another strategy

If the task is only to switch the strategy class in a `ServerApp`, this is the
right place. If the task requires new app wiring or a new `ClientApp` entry
point, first visit the app-development sub-skill.

## 2. Send per-round configuration

A common pattern is to keep the main app code fixed and send round-specific
configuration through the strategy:

```python
strategy = FedAvg()
result = strategy.start(
    grid=grid,
    initial_arrays=arrays,
    train_config=ConfigRecord({"lr": 0.1}),
    evaluate_config=ConfigRecord({"eval": True}),
    num_rounds=10,
)
```

Use this when the config changes rarely or only by a few top-level knobs.

## 3. Change the config during training

If a value should change as rounds advance, subclass the strategy and override
`configure_train` or `configure_evaluate`.

Typical use cases:

- learning-rate decay
- per-round sampling tweaks
- different client arguments for training versus evaluation

The override should:

1. inspect the incoming `ConfigRecord`,
2. mutate only the keys that need to change,
3. delegate to the parent implementation when possible.

## 4. Add client mods

Use mods when the behavior is orthogonal to the app logic. Common uses:

- logging or inspection before/after a task
- message-size accounting
- lightweight instrumentation or policy checks

Application-wide mods apply first; function-specific mods wrap the selected
handler inside them. That order matters when debugging unexpected message
changes.

## 5. Wrap a strategy with privacy or secure aggregation

Use the privacy/secure-aggregation wrappers when the strategy itself should be
kept but the round updates need an additional protection layer. The wrappers are
best treated as strategy decorators: start with the underlying strategy and then
add the protection behavior.

## 6. Debug a strategy change

When a strategy change looks right but the results are off:

- print or inspect the `summary()` output;
- check the weights used by the aggregation key;
- verify that the sampling fractions still select the intended number of nodes;
- confirm that the expected config keys are present in the payload.

## When to hand off

If the user now needs local runtime routing, `flwr run`, or SuperLink/SuperNode
options, switch to the simulation-and-deployment sub-skill.
