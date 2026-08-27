# Cross-cutting troubleshooting for Snips NLU

## Purpose

Use this root troubleshooting page for problems that happen before a specific dataset/API/CLI workflow is selected, or for failures shared across multiple sub-skills. For workflow-specific fixes, route to the nearest sub-skill troubleshooting page.

## Install/import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'snips_nlu'` | Package is not installed in the active Python. | Install `snips-nlu`, then run `python scripts/check_snips_nlu_environment.py --json`. |
| Old dependency fails to build on a modern Python | Snips NLU `0.20.x` pins old `scikit-learn`/compiled dependencies. | Prefer a Python 3.8 CPU environment for this release. Avoid treating Python 3.11+ install failure as a package API problem. |
| `ImportError` from `sklearn`, `sklearn_crfsuite`, `snips_nlu_parsers`, or `snips_nlu_utils` | Base dependencies are missing or incompatible. | Reinstall the base package and run `python -m pip check`. Do not install only the top-level package without dependencies unless doing source inspection. |
| `snips-nlu` command not found but import works | Console script directory is not on PATH. | Use `python -m snips_nlu ...` or fix the environment PATH. |
| CLI help crashes | Package import path is broken or a dependency is missing. | Run the environment helper; check import and `pip check` before debugging command flags. |

## Language resources and built-in entities

| Symptom | Likely cause | Recovery |
|---|---|---|
| `MissingResource` or `Language resource '<lang>' not found` | Language resources were not downloaded or linked. | Run `python -m snips_nlu download <lang>` or link a compatible resource package/directory. |
| Built-in entity examples cannot be generated during YAML conversion | Built-in parser/resource package unavailable for the selected language/entity. | Use a supported language, install resources, or provide explicit custom entity values where appropriate. |
| Built-in entity extraction returns unresolved or missing slots | Required resources or parser compatibility may be missing, or the entity is not supported for the language. | Verify language code and resources; see `sub-skills/dataset-and-resources/references/resources-and-entities.md`. |

Do not make diagnostic helpers download resources automatically. Downloads are network operations and should be explicit user choices.

## Version and persisted model compatibility

Snips NLU separates the Python package version (`0.20.2` here) from the persisted model format version (`0.20.0` here). A persisted engine stores a `model_version` in its `nlu_engine.json`.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `IncompatibleModelError` while loading an engine | Persisted model format differs from the installed library's expected model version. | Use a matching Snips NLU version, retrain/persist the engine, or only as a risky inspection step pass the bypass flag described in `sub-skills/engine-api/references/configuration-and-persistence.md`. |
| `LoadingError: Missing nlu engine model file` | The path does not point to a complete persisted engine directory. | Check for `nlu_engine.json` and parser/entity subdirectories; use `engine.persist()` or `snips-nlu train` to create a valid artifact. |
| `PersistingError` or output path already exists | Snips NLU refuses to persist over existing directories. | Choose a fresh output directory or deliberately remove/archive the old one. |

## Dataset/API/CLI route selection

- Dataset YAML/JSON schema, entity values, language codes, and conversion failures: use `sub-skills/dataset-and-resources/references/troubleshooting.md`.
- Python API errors such as `NotTrained`, `InvalidInputError`, `IntentNotFoundError`, `PersistingError`, `LoadingError`, and training nondeterminism: use `sub-skills/engine-api/references/troubleshooting.md`.
- CLI flag parsing, intent filters, resource download commands, training/parsing command failures, and metrics extras: use `sub-skills/cli-workflows/references/troubleshooting.md`.

## Safe diagnostic sequence

```bash
python scripts/check_snips_nlu_environment.py --json
python -m snips_nlu version
python -m snips_nlu model-version
python -m snips_nlu --help
```

If the task uses a specific language resource and network/downloads are allowed:

```bash
python -m snips_nlu download en
python scripts/check_snips_nlu_environment.py --resource en --json
```

If network is not allowed, stop at resource availability checks and explain the limitation instead of attempting training/parsing workflows that require missing resources.
