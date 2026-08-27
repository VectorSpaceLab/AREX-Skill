# Output and UI

## Pickle result object

YiVal serializes `Experiment` objects with `pickle` when `output_path` is set. Use the indexed filename:

```python
import pickle

with open("results_0.pkl", "rb") as f:
    experiment = pickle.load(f)
```

Key fields:

- `experiment.group_experiment_results`: grouped by input data representation.
- `experiment.combination_aggregated_metrics`: metrics grouped by variation combination.
- `experiment.selection_output`: AHP or custom selection output when configured.
- `experiment.enhancer_output`: prompt/combination enhancement result when an enhancer runs.

## Dash display

`display_results_dash()` starts a Dash app. It:

- finds an available port starting at `8074`;
- builds function argument metadata from the configured `custom_function` and dataset;
- removes duplicate enhancer results before display;
- optionally exposes ngrok if environment variable `ngrok` is set.

Headless agents should set `display=False` to avoid blocking.

## Interactive mode

For `dataset.source_type: user_input`, `ExperimentRunner` creates an empty `Experiment` and starts Dash in interactive mode. The UI asks for function inputs and applies variations without preloaded rows.

## Bot mode

`yival bot config.yml` routes through `ExperimentRunner` with `interactive=True` and `display=False` by default. Use it only after the underlying experiment config can run.

## Human ratings

Configs can include:

```yaml
human_rating_configs:
  - name: clarity
    instructions: Rate whether the result is clear.
    scale: [1, 5]
```

These are UI-facing rating prompts, not automatic metrics by themselves.
