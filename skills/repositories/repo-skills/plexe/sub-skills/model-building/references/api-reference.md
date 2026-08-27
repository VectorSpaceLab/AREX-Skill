# Plexe API reference

This reference captures the public and workflow-adjacent APIs that are most useful when
using Plexe as a package or from the CLI.

## Top-level entry points

### `plexe.main.main`

```python
main(
    intent: str,
    data_refs: list[str] | None = None,
    integration: WorkflowIntegration | None = None,
    spark_mode: str = "local",
    user_id: str = "default_user",
    experiment_id: str = "local",
    max_iterations: int = 10,
    global_seed: int | None = None,
    work_dir: Path = Path("/tmp/model_builder_v2"),
    train_dataset_uri: str | None = None,
    val_dataset_uri: str | None = None,
    test_dataset_uri: str | None = None,
    enable_final_evaluation: bool = False,
    nn_default_epochs: int | None = None,
    nn_max_epochs: int | None = None,
    allowed_model_types: list[str] | None = None,
    is_retrain: bool = False,
    original_model_uri: str | None = None,
    original_experiment_id: str | None = None,
    auto_mode: bool = True,
    user_feedback: dict | None = None,
    enable_otel: bool = False,
    otel_endpoint: str | None = None,
    otel_headers: dict[str, str] | None = None,
    external_storage_uri: str | None = None,
    csv_delimiter: str = ",",
    csv_header: bool = True,
)
```

Returns `(best_solution, final_metrics, evaluation_report)`.

Important notes:

- Prefer `train_dataset_uri` over deprecated `data_refs`.
- `test_dataset_uri` auto-enables final evaluation.
- `is_retrain=True` switches to retraining mode.
- `integration=None` defaults to `StandaloneIntegration`.
- `spark_mode` may be `local` or `databricks`.

### `plexe.workflow.build_model`

```python
build_model(
    spark: SparkSession,
    train_dataset_uri: str,
    val_dataset_uri: str | None,
    test_dataset_uri: str | None,
    user_id: str,
    intent: str,
    experiment_id: str,
    work_dir: Path,
    runner: TrainingRunner,
    search_policy: SearchPolicy,
    config: Config,
    integration: WorkflowIntegration,
    enable_final_evaluation: bool = False,
    on_checkpoint_saved: Callable[[str, Path, Path], None] | None = None,
    pause_points: list[str] | None = None,
    on_pause: Callable[[str], None] | None = None,
    user_feedback: dict | None = None,
) -> tuple[Solution, dict, EvaluationReport | None] | None
```

Returns `None` only when the workflow pauses for feedback.

### `plexe.retrain.retrain_model`

```python
retrain_model(
    original_model_uri: str,
    train_dataset_uri: str,
    experiment_id: str,
    work_dir: Path,
    runner,
    config,
    on_checkpoint_saved=None,
) -> tuple[Solution, dict]
```

This path expects the original package to contain retraining support files.

## Configuration and routing

### `plexe.config.Config`

Pydantic settings model used by the workflow.

Key methods:

- `get_temperature(agent_name: str) -> float`
- `settings_customise_sources(...)`
- model validators that enforce `nn_default_epochs <= nn_max_epochs`
- environment parsing for OTEL headers

Important fields:

- search: `max_search_iterations`, `max_parallel_variants`, `global_seed`
- training: `training_timeout`, `nn_default_epochs`, `nn_max_epochs`, `nn_default_batch_size`
- backend: `spark_mode`, `spark_local_cores`, `spark_driver_memory`, `databricks_*`
- model families: `allowed_model_types`
- data parsing: `csv_delimiter`, `csv_header`
- observability: `enable_otel`, `otel_endpoint`, `otel_headers`
- routing: `routing_config`

### `plexe.config.RoutingConfig`

- `default: RoutingProviderConfig | None`
- `providers: dict[str, RoutingProviderConfig]`
- `models: dict[str, str]`

### `plexe.config.RoutingProviderConfig`

- `api_base: str | None`
- `headers: dict[str, str]`

### `plexe.config.get_routing_for_model(config, model_id)`

Resolves the effective API base and headers for a model id.

### `plexe.config.get_config()`

Loads the effective runtime config from CLI/env/YAML/defaults.

## Workflow integration

### `plexe.integrations.base.WorkflowIntegration`

Abstract interface with these required methods:

- `prepare_workspace(experiment_id, work_dir)`
- `get_artifact_location(artifact_type, dataset_uri, experiment_id, work_dir)`
- `ensure_local(uris, work_dir)`
- `prepare_original_model(model_reference, work_dir)`
- `on_checkpoint(experiment_id, phase_name, checkpoint_path, work_dir)`
- `on_completion(experiment_id, work_dir, final_metrics, evaluation_report)`
- `on_failure(experiment_id, error)`
- `on_pause(phase_name)`

### `plexe.integrations.standalone.StandaloneIntegration`

```python
StandaloneIntegration(external_storage_uri: str | None = None, user_id: str | None = None)
```

Behavior notes:

- Local mode keeps artifacts on the filesystem.
- `external_storage_uri` currently supports `s3://`.
- `prepare_original_model()` can resolve a local path, S3 URI, or experiment id.

## Core data models

### `plexe.models.DataLayout`

- `flat_numeric`
- `image_path`
- `text_string`
- `unsupported`

### `plexe.models.TaskType`

- `binary_classification`
- `multiclass_classification`
- `regression`
- `learning_to_rank`

### `plexe.models.Metric`

- `name: str`
- `optimization_direction: str`

### `plexe.models.BuildContext`

Important fields:

- identifiers: `user_id`, `experiment_id`, `dataset_uri`, `work_dir`, `intent`
- data understanding: `data_layout`, `viable_model_types`, `primary_input_column`, `stats`, `task_analysis`, `metric`, `output_targets`, `group_column`, `excluded_columns`
- splits and samples: `train_uri`, `val_uri`, `test_uri`, `train_sample_uri`, `val_sample_uri`
- feature engineering: `feature_pipeline`, `train_transformed_uri`, `val_transformed_uri`, `test_transformed_uri`
- baseline/search: `heuristic_baseline`, `baseline_performance`, `insight_store`
- orchestration: `feedback`, `scratch`

Key methods:

- `add_outer_loop_feedback(solution, issue)`
- `update(**kwargs)`
- `to_dict()` / `from_dict()`

### `plexe.models.Solution`

Important fields:

- `solution_id`, `feature_pipeline`, `model`, `model_type`
- `model_artifacts_path`, `performance`, `train_performance`, `training_time`
- `parent`, `children`, `stage`, `plan`, `error`, `is_buggy`
- Keras/PyTorch extras: `optimizer`, `loss`, `epochs`, `batch_size`

Useful properties:

- `is_leaf`
- `debug_depth`
- `is_successful`

### Search-planning models

- `Insight`
- `Hypothesis`
- `FeaturePlan`
- `ModelPlan`
- `UnifiedPlan`
- `Baseline`

### Evaluation models

- `CoreMetricsReport`
- `DiagnosticReport`
- `RobustnessReport`
- `ExplainabilityReport`
- `BaselineComparisonReport`
- `EvaluationReport`

### Error classes

- `TrainingError`
- `ValidationError`
- `RetrainingError`

## Search and journal helpers

### `plexe.search.tree_policy.TreeSearchPolicy`

Default tree-search strategy used by the workflow.

### `plexe.search.evolutionary_search_policy.EvolutionarySearchPolicy`

Alternative adaptive policy kept as an implementation option.

### `plexe.search.journal.SearchJournal`

Tracks the search tree, best solution, and success/failure counts.

## Runtime helpers

### Spark session helpers

- `get_or_create_spark_session(config=None)`
- `stop_spark_session()`

### Dataset normalization

- `DatasetNormalizer.normalize(input_uri, output_uri, format_hint=None, read_options=None)`
- `FormatDetector.detect(uri)`
- `DatasetReader.read(uri, format, options=None)`

### Training runner

- `LocalProcessRunner.run_training(...)`

This runner creates a temporary per-run directory and launches the appropriate training
script in a subprocess.

### Validation helpers

- `canonicalize_split_ratios(split_ratios)`
- `validate_dataset_splits(...)`
- `validate_sklearn_pipeline(...)`
- `validate_pipeline_consistency(...)`
- `validate_model_definition(model_type, definition)`
- `validate_metric_function_object(func)`
- `validate_keras_model(model, task_analysis)`
- `validate_keras_optimizer(optimizer)`
- `validate_keras_loss(loss)`

### Metric and evaluation helpers

- `select_viable_model_types(data_layout, selected_frameworks=None)`
- `metric_requires_probabilities(metric_name)`
- `normalize_probability_predictions(y_true, y_pred_proba, metric_name)`
- `evaluate_on_sample(...)`
- `compute_metric_hardcoded(...)`

## What future agents should remember

- The package is a workflow engine, not just a model wrapper.
- The main workflow always expects a working data layout + metric + model-family decision.
- The final package is self-contained and should be inspected through the bundled artifacts,
  not by reaching back into the source repository.

