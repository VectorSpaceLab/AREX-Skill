# Cross-Cutting Troubleshooting

Read this before installing broad extras, running network-bound Hub commands, loading untrusted modules, launching evaluator pipelines, or debugging cache/distributed behavior.

## Install And Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'evaluate'` | Package is not installed in the active Python. | Install with `pip install evaluate`, then run `python -c "import evaluate; print(evaluate.__version__)"`. |
| `ImportError` for a metric-specific package such as `sacrebleu`, `seqeval`, `jiwer`, `nltk`, or `bert_score` | The selected evaluation module has optional requirements not installed by base `evaluate`. | Read the module card or requirements, install only that module's dependency, then retry `evaluate.load(...)`. |
| Evaluator construction fails with missing `transformers` or `scipy` | `evaluate[evaluator]` extra is missing. | Install `pip install "evaluate[evaluator]"`; do not install full dev/test extras unless needed. |
| Evaluator pipeline warns that no PyTorch/TensorFlow/Flax backend is available | `transformers` imports, but no model backend is installed. | For real model inference, install one backend appropriate for the project and hardware; for dry inspection, avoid running the pipeline. |
| `evaluate.visualization` import fails for `matplotlib` | Visualization dependency is optional. | Install `matplotlib` only if radar plots are required. |

## Loading And Module Safety

- Evaluation modules are executable Python. Only load trusted local paths or Hub/community modules.
- `code_eval` executes candidate code and requires explicit opt-in through `HF_ALLOW_CODE_EVAL=1`; use sandboxing and user approval.
- If `evaluate.load(...)` cannot find a module, verify spelling, `module_type`, `config_name`, network access, and `revision`.
- If a local module fails after moving files, inspect relative imports and additional files; local dependencies need to be adjacent to the module script or handled by the loader.

## Cache And Distributed Runs

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Cache lock timeout or concurrent file collision | Multiple processes share default `experiment_id` or cache path incorrectly. | Set a stable shared `cache_dir`, common `experiment_id`, same `num_process`, and unique `process_id` values. |
| Non-zero worker returns `None` from `compute()` | Distributed design: only `process_id == 0` returns final results. | Aggregate or read results only on process 0. |
| `keep_in_memory` rejected with distributed settings | In-memory mode is incompatible with `num_process > 1`. | Use file-backed cache for distributed runs. |
| Missing inputs error from `compute()` | Module features do not match provided keyword names. | Inspect `module.features` and `module.inputs_description`; use custom names such as `inputs`/`targets` when required. |

## Hub, CLI, And Credentials

- `evaluate-cli create` is not a dry-run command: it creates a Hub Space, clones it, renders templates, commits, and pushes.
- `evaluate.push_to_hub(...)` mutates Hub model-card metadata and requires credentials and network access.
- CLI import can fail when `cookiecutter` is missing; install `cookiecutter` or the documented template dependencies.
- This checkout imports `huggingface_hub.Repository` in the CLI. If a newer `huggingface_hub` release removes or relocates it, pin to a compatible Hub client or update the source before relying on `evaluate-cli`.
- Module names passed to `evaluate-cli create` must not contain hyphens, and `--module_type` must be one of `metric`, `comparison`, or `measurement`.

## Offline Or CI-Safe Workflows

- Prefer local module paths and tiny fixture data for CI.
- Avoid `list_evaluation_modules(include_community=True)`, model IDs, dataset names, `evaluate-cli create`, and `push_to_hub` when network is disabled.
- Use bundled helper scripts for local inspection: `scripts/check_evaluate_environment.py`, `sub-skills/module-loading/scripts/local_module_smoke.py`, `sub-skills/module-computation/scripts/compute_smoke.py`, `sub-skills/evaluator-pipelines/scripts/inspect_evaluator_tasks.py`, and `sub-skills/hub-and-cli/scripts/inspect_evaluate_cli.py`.
