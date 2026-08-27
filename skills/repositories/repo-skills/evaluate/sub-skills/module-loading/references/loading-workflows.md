# Loading Workflows

This reference focuses on choosing and importing Evaluate modules. It intentionally stops before `compute`, `add`, `add_batch`, cache-file synchronization, and distributed result aggregation; route those details to `../module-computation/`.

## API Surface

| API | Purpose | Notes |
| --- | --- | --- |
| `evaluate.load(path, config_name=None, module_type=None, process_id=0, num_process=1, cache_dir=None, experiment_id=None, keep_in_memory=False, download_config=None, download_mode=None, revision=None, **init_kwargs)` | Returns an `EvaluationModule` instance. | Evidence: `src/evaluate/loading.py`. |
| `evaluate.list_evaluation_modules(module_type=None, include_community=True, with_details=False)` | Lists available Hub modules. | Evidence: `src/evaluate/inspect.py`. Requires Hub/network access. |
| `evaluate.inspect_evaluation_module(path, local_path, download_config=None, **download_kwargs)` | Copies module processing scripts to a local directory for review/modification. | Evidence: `src/evaluate/inspect.py`. |

Valid `module_type` values are `metric`, `comparison`, and `measurement`. If `module_type` is omitted for a canonical one-part name, Evaluate tries canonical Hub namespaces in that order. If a loaded instance reports a different type than the requested `module_type`, `evaluate.load()` raises `TypeError`.

## Choose The Loader Path

### Built-In Or Canonical Hub Module

Use a one-part name for modules hosted in the Evaluate canonical namespaces:

```python
import evaluate

accuracy = evaluate.load("accuracy")
rouge = evaluate.load("rouge", module_type="metric")
exact_match = evaluate.load("exact_match", module_type="comparison")
word_length = evaluate.load("word_length", module_type="measurement")
```

Canonical modules are stored on the Hub under type-specific namespaces such as `evaluate-metric`, `evaluate-comparison`, and `evaluate-measurement`. In the source checkout, representative implementations live under `metrics/`, `comparisons/`, and `measurements/`.

### Community Hub Module

Use a two-part repo ID for community modules:

```python
import evaluate

module = evaluate.load("lvwerra/element_count", module_type="measurement")
```

Community loading requires that the Hub repo is reachable and compatible with the installed Evaluate version. Pin `revision=` when reproducibility matters:

```python
module = evaluate.load("owner/custom_metric", module_type="metric", revision="main")
```

### Local Directory Or Script

Use a local path when a user has a metric script or an inspected/edited module. Evaluate accepts either the script itself or a directory containing a script with the same basename as the directory:

```python
import evaluate

local_metric = evaluate.load("./my_metric/my_metric.py")
local_metric = evaluate.load("./my_metric", module_type="metric")
```

A local metric class should subclass an Evaluate module base such as `evaluate.Metric`, define `_info()`, and define `_compute()`. See `scripts/local_module_smoke.py` for a tiny self-contained fixture that writes and loads such a module without network access.

## Discover And Inspect Before Loading

List canonical-only modules of one type:

```python
import evaluate

modules = evaluate.list_evaluation_modules(
    module_type="comparison",
    include_community=False,
    with_details=True,
)
```

With `with_details=True`, entries include `name`, `type`, `community`, and `likes`. With `include_community=False`, canonical module IDs are returned without the `evaluate-{type}/` namespace.

Inspect a module script before executing unfamiliar code:

```python
import evaluate

evaluate.inspect_evaluation_module("accuracy", local_path="./accuracy_inspect")
# Review the copied script, requirements, and imports before evaluate.load("./accuracy_inspect").
```

For community or local modules, inspect source and requirements before loading because loading imports executable Python.

## Config Names

Use `config_name` when a module has variants. Evidence examples:

- `metrics/glue/glue.py` requires one of `sst2`, `mnli`, `mnli_mismatched`, `mnli_matched`, `cola`, `stsb`, `mrpc`, `qqp`, `qnli`, `rte`, `wnli`, or `hans`.
- `metrics/bleurt/README.md` documents checkpoint-like configs such as `bleurt-base-128`, `bleurt-large-512`, and `BLEURT-20`.
- Several metrics support structural configs such as `multilabel` or `multilist` that change expected features.

Pattern:

```python
glue = evaluate.load("glue", config_name="mrpc")
print(glue.features)
```

After loading, inspect `.features` and `.inputs_description`; they are the source of truth for input names and element types.

## Dynamic Module Cache Behavior

Evaluate copies/imports module code through a dynamic modules cache so modules can be imported as Python packages without manual `sys.path` changes. Relevant behavior from `src/evaluate/loading.py`:

- Local scripts are loaded through `LocalEvaluationModuleFactory`.
- Hub scripts are loaded through `HubEvaluationModuleFactory`.
- If Hub loading fails due to connection or file-not-found conditions, Evaluate attempts `CachedEvaluationModuleFactory` for previously cached canonical or community modules.
- `download_mode` defaults to reuse existing cached files when possible.
- `download_config` can pass a custom download/cache configuration.

If cache state appears stale, rerun with a fresh cache directory or clear only the relevant Hugging Face module cache after confirming no other process depends on it.

## Safe Local Smoke Helper

Run the bundled helper when a future agent needs to verify local module loading in an environment that already has `evaluate` installed:

```bash
python skills/evaluate/sub-skills/module-loading/scripts/local_module_smoke.py
```

The helper creates a temporary local metric module, loads it from the local directory, computes a deterministic score, prints a compact JSON result, and deletes the temporary directory automatically. It does not contact the Hub and does not depend on the source checkout.
