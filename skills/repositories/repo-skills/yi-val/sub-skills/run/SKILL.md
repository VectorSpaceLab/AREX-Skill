---
name: run
description: "Run YiVal experiments through the CLI or Python APIs, interpret
  result artifacts, and use interactive/Dash/bot workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# YiVal run workflows

Use this sub-skill when the config is ready and the user wants to run YiVal, inspect outputs, resume from saved experiment data, use the Dash/interactive UI, or call `ExperimentRunner` / `LiteExperimentRunner` programmatically.

## Read first

- [Runtime workflows](references/runtime-workflows.md): CLI and API execution patterns.
- [Runner API](references/runner-api.md): `ExperimentRunner`, `LiteExperimentRunner`, state, output pickle behavior.
- [Output and UI](references/output-and-ui.md): result structures, Dash, Streamlit/bot, interactive mode.
- [Runtime troubleshooting](references/troubleshooting.md): run-time failures and fixes.

## Safe pre-run checks

1. Run installation smoke from the skill root: `python scripts/check_install.py`.
2. Validate YAML using the setup sub-skill.
3. Run a tiny no-network fixture from the skill root: `python scripts/write_minimal_experiment.py --run`.
4. For provider-backed configs, verify environment variables and set small `number_of_examples` / `number_of_variations` first.

## CLI run patterns

```bash
yival validate config.yml
yival run config.yml --output_path results.pkl
```

For non-blocking/headless automation, prefer Python API:

```python
from yival.experiment.experiment_runner import ExperimentRunner

runner = ExperimentRunner("config.yml")
runner.run(display=False, interactive=False, output_path="results.pkl", experiment_input_path="")
```

Why: CLI `--display` defaults to `True`, so it may start Dash and block until the UI server exits.

## Programmatic runner selection

| Need | Use |
| --- | --- |
| YAML-driven full experiment | `ExperimentRunner(config_path).run(...)` |
| Existing in-memory data/evaluator/config | `LiteExperimentRunner(...).run_experiment(enable_selector=True/False)` |
| Async custom function | `ExperimentRunner.run(async_eval=True)` and ensure the custom function is coroutine-compatible |
| Reuse saved experiment pickle | `ExperimentRunner.run(experiment_input_path="previous.pkl", ...)` |
| Interactive user input | `dataset.source_type: user_input` or `yival demo --basic_interactive` |
| Chat/bot over experiment output | `yival bot config.yml` after checking UI constraints |

## Runtime sequence inside `ExperimentRunner`

1. Load one or more configs with `load_and_validate_configs()`.
2. Register custom components from the YAML.
3. Build `Evaluator` and `ExperimentState`.
4. Build all variation combinations from the state.
5. Process data with `DataProcessor` unless reusing an experiment pickle.
6. Call the custom function for each data row / combination.
7. Evaluate individual results and aggregate metrics into an `Experiment`.
8. Apply selection strategy, enhancer, and optional trainer when configured.
9. Write pickle output and optionally launch Dash/interactive/bot UI.

## Output interpretation

- `output_path="results.pkl"` writes `results_0.pkl` for the first config.
- Each `ExperimentResult` contains `input_data`, `combination`, `raw_output`, `latency`, `token_usage`, and `evaluator_outputs`.
- `Experiment.combination_aggregated_metrics` is where AHP selection reads metrics such as `average_token_usage`, `average_latency`, and aggregated evaluator names.
- `Experiment.selection_output.best_combination` is a stringified combination key when a selection strategy runs.

## When to route elsewhere

- If the config will generate examples or prompt variations, read [prompt-automation](../prompt-automation/SKILL.md).
- If selecting metrics, evaluators, human ratings, or enhancers is the main issue, read [evaluation-optimization](../evaluation-optimization/SKILL.md).
- If custom components fail to register or import, read [custom-components](../custom-components/SKILL.md).
- If the user asks for fine-tuning/training, state that it is optional and heavy, then require explicit approval for trainer extras, credentials, downloads, GPU, and cost before proceeding.
