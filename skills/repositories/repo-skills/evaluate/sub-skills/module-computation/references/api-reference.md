# Computation API Reference

This reference covers the computation surface for loaded `evaluate` modules. Loading and discovery are owned by `../module-loading/`.

## Evaluation Module Classes

`EvaluationModule` is the base class for all computation modules. `Metric`, `Comparison`, and `Measurement` inherit the same computation/cache API and differ by `module_type` and module semantics.

### Constructor Settings

| Setting | Default | Use |
| --- | --- | --- |
| `config_name` | `None` -> `"default"` | Select a module configuration and cache namespace. |
| `keep_in_memory` | `False` | Store streamed examples in memory instead of Arrow cache files; invalid with `num_process > 1`. |
| `cache_dir` | evaluate metrics cache | Directory for temporary Arrow data; must be shared across workers in distributed runs. |
| `num_process` | `1` | Total worker count for distributed computation. |
| `process_id` | `0` | Current worker id; must be an integer from `0` to `num_process - 1`. |
| `seed` | current NumPy state | Temporarily applied while `_compute` runs. |
| `experiment_id` | `"default_experiment"` | Cache/lock namespace; set unique ids for concurrent distributed evaluations. |
| `hash` | `None` | Internal loaded-module content hash. |
| `max_concurrent_cache_files` | `10000` | Retry ceiling for concurrent single-process cache files. |
| `timeout` | `100` | Seconds to wait for distributed cache-file synchronization. |
| `**kwargs` | none | Module-specific constructor options, when exposed by a loaded module. |

## Methods

### `compute(self, *, predictions=None, references=None, **kwargs) -> Optional[dict]`

Runs the module and returns a result dictionary on `process_id == 0`; returns `None` on non-zero distributed workers. If `predictions` or `references` are provided, `compute` validates required inputs, internally writes them as one batch, finalizes storage, and calls the module's `_compute` implementation. If no inputs are provided, it computes over examples previously stored by `add` or `add_batch`.

Use `**kwargs` for either non-standard feature inputs or module-specific compute options. For modules whose `features` are not `predictions`/`references`, pass the exact feature names, such as `compute(inputs=[...], targets=[...])`.

### `add(self, *, prediction=None, reference=None, **kwargs)`

Adds one example to the module's cache or in-memory buffer. Standard modules accept singular `prediction=` and `reference=`. Modules with other feature names use those names through `**kwargs`, such as `add(inputs=1, targets=1)`.

### `add_batch(self, *, predictions=None, references=None, **kwargs)`

Adds a batch of examples. Standard modules accept plural `predictions=` and `references=`. The batch columns must have matching lengths and match the module's `features`; otherwise evaluate raises a `ValueError` with the expected format and summarized inputs.

### `download_and_prepare(...)`

Optional module resource preparation. Most users do not call this manually; loaded modules call the relevant preparation path when needed.

## Module Metadata for Computation

Use these properties before computing:

| Property | Why it matters |
| --- | --- |
| `module.features` | Defines required input names and one-example schema. |
| `module.inputs_description` | Documents module-specific arguments and usage. |
| `module.module_type` | Distinguishes `metric`, `comparison`, or `measurement`. |
| `module.name` | Used in combined-result prefixes and cache paths. |
| `module.experiment_id` | Shows the active cache namespace. |
| `module.streamable` | Metadata flag for streamability expectations. |
| `module.info` | Full `EvaluationModuleInfo`, `MetricInfo`, `ComparisonInfo`, or `MeasurementInfo`. |

`EvaluationModuleInfo.features` may be a single `datasets.Features` object or a list of acceptable `Features` alternatives. If multiple alternatives are present, evaluate picks the first schema that can encode the example.

## Combined Evaluations

### `evaluate.combine(evaluations, force_prefix=False)`

Returns a `CombinedEvaluations` object. `evaluations` can be a list or dictionary of module names or loaded module objects.

- List input uses each module's `name` as the prefix when needed.
- Dict input uses dict keys as module names/prefixes.
- `force_prefix=False` keeps unique output keys unprefixed and prefixes only duplicate keys.
- `force_prefix=True` prefixes every output key.

### `CombinedEvaluations.compute(predictions=None, references=None, **kwargs)`

Runs every contained module with the subset of inputs matching each module's feature names, then merges the result dictionaries. If two modules return the same key, keys are prefixed with module names. If the same module name appears more than once, an index is added, such as `accuracy_0_accuracy`.

`CombinedEvaluations` also supports `add(prediction=None, reference=None, **kwargs)` and `add_batch(predictions=None, references=None, **kwargs)` with the same final `compute()` pattern.

## Saving Results

### `evaluate.save(path_or_file, **data)`

Writes a JSON file and returns the path. If `path_or_file` has a suffix, it is treated as a file path. Otherwise evaluate creates the directory and writes `result-%Y_%m_%d-%H_%M_%S.json` inside it. The saved JSON includes user-provided keys plus metadata keys:

- `_timestamp`
- `_git_commit_hash`
- `_evaluate_version`
- `_python_version`
- `_interpreter_path`

Because `_interpreter_path` is machine-specific, review saved JSON before sharing it publicly.

## Input Containers and Casting

Evaluate accepts Python lists and, when installed, NumPy arrays, PyTorch tensors, and TensorFlow tensors. Inputs are converted through `datasets.Features`/Arrow before computation. String features are guarded: evaluate rejects non-string objects for `Value("string")` instead of silently casting arbitrary objects to strings. `Sequence(...)` features expect list-like values, not scalar strings.

