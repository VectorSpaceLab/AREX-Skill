# YiVal workflow map

## Core execution model

YiVal organizes prompt/model experiments around a small set of stages:

1. **Data generation/loading**
   - `dataset.source_type: dataset` uses a registered `BaseReader` such as `csv_reader` or `huggingface_dataset_reader`.
   - `dataset.source_type: machine_generated` uses a registered `BaseDataGenerator` such as `openai_prompt_data_generator` or `document_data_generator`.
   - `dataset.source_type: user_input` opens an interactive UI path instead of preloading rows.
2. **Combination creation**
   - YAML `variations` entries define wrapper names and either manual `WrapperVariation` values or a `generator_name` plus `generator_config`.
   - `ExperimentState.set_experiment_config()` initializes variations and `get_all_variation_combinations()` computes the Cartesian product.
3. **Analysis/custom function call**
   - `ExperimentRunner` calls the configured `custom_function` with row values unpacked as keyword arguments and `state=<ExperimentState>`.
   - The custom function should return `MultimodalOutput`; `text_output` is what text evaluators read.
   - `StringWrapper(name=<variation name>, state=state)` resolves the active prompt/value for the current combination.
4. **Evaluation**
   - `Evaluator` dispatches individual, comparison, and all-results evaluators by registry id.
   - Individual evaluators attach `EvaluatorOutput` to each `ExperimentResult`.
   - Comparison and all-results evaluators can mutate or annotate grouped/global result structures.
5. **Aggregation and selection**
   - `generate_experiment()` groups results by input, aggregates metrics by combination, and records average latency/token usage.
   - `AHPSelection` can choose a `best_combination` from configured criteria and weights.
6. **Enhancement/training/UI**
   - Enhancers can create improved prompt/combination candidates from prior experiment results.
   - Trainers are optional and out-of-scope unless explicitly requested.
   - Dash and Streamlit/bot entry points display, compare, or interact with experiment data.

## Key runtime objects

| Object | Module | Role |
| --- | --- | --- |
| `ExperimentConfig` | `yival.schemas.experiment_config` | Top-level YAML config object; holds dataset, custom function, variations, evaluators, selection, enhancer, trainer, and custom registries. |
| `DatasetConfig` | `yival.schemas.dataset_config` | Selects `dataset`, `machine_generated`, or `user_input` source behavior. |
| `InputData` | `yival.schemas.common_structures` | One input example; `content` maps to custom function kwargs and `expected_result` feeds expected-result metrics. |
| `WrapperVariation` | `yival.schemas.experiment_config` | One instantiated value for a wrapper namespace. |
| `ExperimentState` | `yival.states.experiment_state` | Holds active variations and yields the right value to wrappers during each combination. |
| `StringWrapper` | `yival.wrappers.string_wrapper` | Replaces or formats prompt strings using the active variation. |
| `MultimodalOutput` | `yival.schemas.experiment_config` | Standard result object for text, images, videos, and optional context. |
| `ExperimentResult` | `yival.schemas.experiment_config` | One input/combination output with latency, token usage, and evaluator outputs. |
| `Experiment` | `yival.schemas.experiment_config` | Aggregated experiment with grouped results, combination metrics, selection output, and enhancer output. |

## Cross-sub-skill responsibilities

- Use **setup** to create valid YAML and choose data source fields.
- Use **run** to execute YAML configs, interpret outputs, and choose between CLI and programmatic runners.
- Use **prompt-automation** when the YAML uses data generators or variation generators.
- Use **evaluation-optimization** when the YAML uses evaluators, selection strategies, human ratings, or enhancers.
- Use **custom-components** when YAML includes `custom_reader`, `custom_wrappers`, `custom_evaluators`, `custom_data_generators`, `custom_variation_generators`, `custom_selection_strategies`, or `custom_enhancers`.

## Practical constraints

- Importing `yival.cli` imports most built-in components. A missing optional dependency can break root CLI help before any subcommand runs.
- The built-in OpenAI paths use the legacy `openai.ChatCompletion.create` API from `openai==0.27.10`; newer OpenAI SDK clients may not be compatible without code changes.
- Registry dictionaries are process-local. If a script checks registries before importing implementation modules, registries may look empty.
- Dataset file paths in `CSVReader` are first resolved relative to the installed package root, then as user-specified paths. Prefer absolute paths in generated experiment configs when running outside a checkout.
- `ExperimentRunner.run()` writes output pickle names as `<output_stem>_<config_index>.pkl` when `output_path` is supplied.
