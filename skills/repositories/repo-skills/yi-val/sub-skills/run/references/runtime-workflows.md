# Runtime workflows

## Full YAML run with no UI

```python
from yival.experiment.experiment_runner import ExperimentRunner

runner = ExperimentRunner("config.yml")
runner.run(
    display=False,
    interactive=False,
    output_path="results.pkl",
    experiment_input_path="",
    async_eval=False,
    enhance_page=False,
)
```

This is the safest automation path because it avoids Dash and writes a pickle result.

## CLI run with UI

```bash
yival run config.yml --output_path results.pkl
```

The CLI default displays Dash results. Use it for local interactive analysis, not unattended runs.

## Reusing saved experiment results

If `experiment_input_path` is supplied and the indexed pickle exists, `ExperimentRunner` loads it instead of processing the dataset again.

```python
runner.run(
    display=False,
    output_path="new_results.pkl",
    experiment_input_path="previous_results.pkl",
)
```

For config index `0`, YiVal looks for `previous_results_0.pkl`.

## Async evaluation

`ExperimentRunner._aprocess_dataset()` calls `arun_single_input()` and uses an async rate limiter. Use only if the custom function is coroutine-compatible or safely callable from the async wrapper.

```python
runner.run(display=False, async_eval=True, output_path="async_results.pkl")
```

## Interactive user-input mode

Config requirement:

```yaml
dataset:
  source_type: user_input
```

`ExperimentRunner` skips preloaded data and calls `display_results_dash(..., interactive=True)`. The custom function signature is still inspected to build UI inputs.

## Packaged demos

| Demo flag | What it uses | Provider needs |
| --- | --- | --- |
| `yival demo --basic_interactive` | translation config with `user_input` and `StringWrapper` variations | OpenAI key for the packaged custom function |
| `yival demo --qa_expected_results` | CSV reader + string expected result evaluator | OpenAI key for the packaged QA custom function |
| `yival demo --auto_prompts` | OpenAI data generator, prompt variation generator, OpenAI evaluators, AHP, enhancer | OpenAI key and network |

Prefer the root `write_minimal_experiment.py --run` fixture for offline smoke tests.
