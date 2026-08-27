# Module Loading Troubleshooting

Use this reference when `evaluate.load()`, `list_evaluation_modules()`, or `inspect_evaluation_module()` fails before computation starts.

## Wrong `module_type`

Symptoms:

- `ValueError: Invalid module type ... Has to be one of ...`
- `TypeError` saying the requested type was not found and a different module type was found instead.
- A one-part name loads a module category different from the user's intent.

Fixes:

1. Use exactly one of `metric`, `comparison`, or `measurement`.
2. Pass `module_type=` explicitly for comparisons and measurements, and for metrics when a name may be ambiguous.
3. Use `evaluate.list_evaluation_modules(module_type=..., include_community=False)` to verify canonical availability.

## Wrong Path Or Name

Symptoms:

- `FileNotFoundError: Couldn't find a metric script at ...`
- `FileNotFoundError` saying the module does not exist on the Hub either.
- Local directory load fails even though a Python file exists nearby.

Fixes:

1. For a local directory, ensure the script basename matches the directory basename, such as `my_metric/my_metric.py`.
2. For a direct local script, pass the `.py` file path.
3. For a canonical module, use the bare name such as `accuracy`; for a community Hub module, use `owner/repo`.
4. For comparison or measurement names, pass `module_type` so Evaluate searches the correct canonical namespace.

## Optional Dependency Errors

Symptoms:

- `ImportError`, `ModuleNotFoundError`, or dependency-specific exceptions during load or preparation.
- A module loads on one machine but fails on another.
- A module starts downloading models or resources unexpectedly.

Fixes:

1. Inspect the module's README/card, imports, and `requirements.txt`.
2. Install only the specific optional dependency the module requires, after user approval.
3. Check whether `config_name` selects a larger model or checkpoint. BLEURT, for example, uses checkpoint-like configs and may require heavy downloads.
4. For NLTK-backed measurements, ensure required tokenizer data can be downloaded or is already present.
5. If the user only needs to prove local module loading, run `scripts/local_module_smoke.py` instead of a dependency-heavy built-in metric.

## Hub, Network, Or Revision Failures

Symptoms:

- HTTP errors from `list_evaluation_modules()` or Hub loading.
- `FileNotFoundError` after a canonical/community lookup.
- A previously working community module changes behavior.

Fixes:

1. Confirm network access and Hub availability.
2. Set `include_community=False` when listing only official modules.
3. Pin `revision=` for reproducible Hub module code.
4. If offline, rely only on local modules or modules already present in the dynamic module cache.
5. If the module is private or gated, ensure the surrounding environment has appropriate Hugging Face authentication; do not put tokens in skill files or logs.

## Dynamic Module Cache And Import Issues

Symptoms:

- Stale code appears to run after editing a local or inspected module.
- Python import errors mention generated module cache paths.
- Offline loads work unexpectedly from cache or fail despite a prior online run.

Fixes:

1. Restart the Python process to clear imported module objects.
2. Use a fresh temporary local module directory name for quick experiments.
3. Pass a fresh cache location through appropriate Evaluate/datasets download configuration if isolation is needed.
4. Remove only the relevant Hugging Face dynamic module cache entry after confirming it is safe for the user's environment.
5. For deterministic local smoke tests, use the bundled script; it creates a unique temporary module directory and exits without persistent source files.

## Unsafe `code_eval`

Symptoms:

- A warning explains that `code_eval` executes untrusted model-generated Python.
- The metric refuses to proceed until `HF_ALLOW_CODE_EVAL=1` is set.

Fixes:

1. Do not bypass the warning in a normal developer environment.
2. Ask the user to confirm they want code execution and provide an isolated sandbox.
3. Run with no sensitive credentials, no writable important directories, restricted network, CPU/memory/time limits, and disposable storage.
4. Set `HF_ALLOW_CODE_EVAL=1` only inside that sandbox and only for the intended command.
5. Treat `metrics/code_eval/execute.py` as reference-only evidence of the risk because it calls `exec()` on generated programs.

## Local Module Smoke Conversion

When a user has a local metric script that fails to load, reduce it to a tiny known-good shape:

1. Create a directory whose name matches the metric file stem.
2. Define a class subclassing `evaluate.Metric`.
3. Return an `evaluate.MetricInfo` with `datasets.Features` from `_info()`.
4. Implement `_compute()` with explicit parameters and no broad `**kwargs`.
5. Load with `evaluate.load("./directory")` and verify a simple deterministic result.

The bundled `scripts/local_module_smoke.py` demonstrates this pattern without contacting the Hub.
