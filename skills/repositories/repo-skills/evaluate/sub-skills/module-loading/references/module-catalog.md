# Module Catalog

Use this catalog to select a loading strategy and identify module-specific risks before calling `evaluate.load()`.

## Module Types

| Type | Base class / info style | Typical input role | Evidence examples |
| --- | --- | --- | --- |
| `metric` | `evaluate.Metric`, `MetricInfo` | Compare model predictions with references or score generations. | `metrics/accuracy/accuracy.py`, `metrics/glue/glue.py`, `metrics/bleurt/README.md`. |
| `comparison` | `evaluate.Comparison`, `ComparisonInfo` | Compare two systems or sets of predictions. | `comparisons/exact_match/exact_match.py`. |
| `measurement` | `evaluate.Measurement`, `MeasurementInfo` | Measure dataset, text, or prediction properties, sometimes without references. | `measurements/word_length/word_length.py`. |

Evaluate documentation describes these categories in `docs/source/a_quick_tour.mdx` and `docs/source/types_of_evaluations.mdx`: metrics measure model performance, comparisons compare model outputs, and measurements analyze dataset/model-output properties.

## Representative Loading Patterns

| Need | Call pattern | Notes |
| --- | --- | --- |
| Generic metric | `evaluate.load("accuracy")` | One-part names search canonical module namespaces; pass `module_type="metric"` to avoid ambiguity. |
| Dataset-specific metric | `evaluate.load("glue", config_name="mrpc")` | Some modules require a valid `config_name`; GLUE raises when missing/invalid. |
| Comparison | `evaluate.load("exact_match", module_type="comparison")` | Prevents accidentally loading a same-named metric if one exists later. |
| Measurement | `evaluate.load("word_length", module_type="measurement")` | Measurements may download resources during preparation, such as NLTK data. |
| Community module | `evaluate.load("owner/repo", module_type="metric")` | Requires Hub access unless cached. Inspect unknown code first. |
| Local script/directory | `evaluate.load("./module_dir")` or `evaluate.load("./module_dir/module_dir.py")` | Directory loading expects script basename to match directory basename. |

## Module Cards And Runtime Attributes

After loading, modules expose metadata from their info object. Useful attributes described in `docs/source/a_quick_tour.mdx` include:

- `description`: theoretical/module summary.
- `citation`: BibTeX or citation text.
- `features`: input feature schema for one example.
- `inputs_description`: argument-level usage text, often the module docstring.
- `homepage`, `license`, `codebase_urls`, `reference_urls`: provenance and licensing context when provided.

Always inspect `features` before building inputs. Some `config_name` values change feature dtypes or structures; for example, GLUE uses float labels for `stsb` but integer labels for many other configs.

## Requirements Files And Optional Dependencies

Many modules import optional libraries at module import, preparation, or compute time. Requirements may be declared in a module-local `requirements.txt`, in imports inside the module script, or in the README/module card. Examples from the checkout:

- `metrics/bleurt/requirements.txt` includes BLEURT from a Git repository, and `metrics/bleurt/README.md` documents large checkpoint downloads selected by `config_name`.
- `measurements/word_length/word_length.py` imports NLTK and downloads `punkt` or `punkt_tab` in `_download_and_prepare()`.
- Several text-generation or similarity metrics depend on packages such as Transformers, Torch, SacreBLEU, or external model checkpoints.

When an `ImportError` or dependency-specific error appears, identify the module directory and inspect its `requirements.txt`, imports, and README before installing anything.

## Built-In Checkout Locations

In the source checkout, built-in module implementations are organized by type:

- `metrics/<name>/<name>.py` for metrics.
- `comparisons/<name>/<name>.py` for comparisons.
- `measurements/<name>/<name>.py` for measurements.

These paths are evidence for skill behavior and examples, not runtime dependencies for the generated skill. Future agents should use installed `evaluate` APIs, local user-provided module paths, or the Hub rather than relying on a source checkout being present.

## Unsafe Or High-Risk Modules

`code_eval` is special and should be treated as unsafe by default:

- `metrics/code_eval/code_eval.py` warns that it executes untrusted model-generated Python.
- `metrics/code_eval/execute.py` contains an `unsafe_execute()` path that calls `exec()` in a subprocess with guardrails.
- The metric requires `HF_ALLOW_CODE_EVAL=1` after the user accepts the risk.

Do not load or compute `code_eval` for an untrusted prompt unless the user explicitly requests it and provides an isolated sandbox with no sensitive filesystem, network, credentials, or long-lived processes.

## Discovery Checklist

Before loading an unfamiliar module:

1. Decide whether the module is canonical, community Hub, or local.
2. Determine whether it is a `metric`, `comparison`, or `measurement`.
3. Check the module card/README and requirements for dependencies, downloads, model checkpoints, and safety warnings.
4. Use `inspect_evaluation_module()` for Hub modules whose code should be reviewed first.
5. Pin `revision=` for reproducible Hub loads.
6. Load, inspect `features` and `inputs_description`, then route computation details to `../module-computation/`.
