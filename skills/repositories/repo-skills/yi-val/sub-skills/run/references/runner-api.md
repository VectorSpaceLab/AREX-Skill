# Runner API reference

## `ExperimentRunner`

Import:

```python
from yival.experiment.experiment_runner import ExperimentRunner
```

Constructor:

```python
runner = ExperimentRunner(config_path: str)
```

Run method:

```python
runner.run(
    display: bool = True,
    interactive: bool = False,
    output_path: str | None = "abc.pkl",
    experiment_input_path: str | None = "abc.pkl",
    async_eval: bool = False,
    enhance_page: bool = False,
)
```

Operational details:

- A YAML list produces multiple configs; each config is processed with an index.
- `output_path="x.pkl"` becomes `x_0.pkl`, `x_1.pkl`, etc.
- `experiment_input_path="x.pkl"` is also indexed as `x_0.pkl`, `x_1.pkl`.
- `display=True` starts a Dash thread for each config with base port `8074 + index`.
- `interactive=True` calls the interactive bot path after results exist, or opens interactive Dash for `user_input` source.
- Custom registries are registered before data processing.

## `LiteExperimentRunner`

Import:

```python
from yival.experiment.lite_experiment import LiteExperimentRunner
```

Constructor:

```python
LiteExperimentRunner(
    config,        # ExperimentConfig-like dict/object
    limiter,       # RateLimiter
    data,          # list[InputData]
    token_logger,  # TokenLogger
    evaluator,     # Evaluator
)
```

Use when the caller already holds data and evaluator objects and wants to avoid YAML file I/O.

```python
experiment = lite_runner.run_experiment(enable_selector=True)
```

`set_variations()` accepts a list of dictionaries shaped like:

```python
[
    {"prompt": ["Prompt A", "Prompt B"]},
    {"model_name": ["gpt-3.5-turbo", "gpt-4"]},
]
```

## Custom function call contract

YiVal calls:

```python
custom_function(**input_data.content, state=tmp_state)
```

So a custom function should:

- accept every dataset field as a named argument;
- accept `state`;
- create `StringWrapper(..., name=<variation-name>, state=state)` for tunable fields;
- return `MultimodalOutput`.

## Token logging

`TokenLogger` is a singleton-style logger used by demos. A custom function should reset/log token usage only if it owns the provider call; otherwise `token_usage` may be zero or stale.
