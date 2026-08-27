---
name: evaluate
description: "Use Hugging Face Evaluate to load metrics, comparisons, and
  measurements; compute and combine results; run evaluator pipelines; create
  custom modules; troubleshoot optional dependencies, cache, Hub, and CLI
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Hugging Face Evaluate

Use this skill when a task involves the `evaluate` Python package: loading evaluation modules, computing metrics/comparisons/measurements, evaluating model pipelines with `evaluate.evaluator`, saving or visualizing results, or creating custom modules for the Hugging Face Hub.

## Start Here

1. Install the package for the workflow the user needs:
   - Base usage: `pip install evaluate`
   - Evaluator pipelines: `pip install "evaluate[evaluator]"` plus a model backend such as PyTorch, TensorFlow, or Flax when actual model inference is required.
   - Module scaffolding: install `cookiecutter`; the full template workflow may also need Gradio for generated widgets.
2. Verify the import before deeper work:

```python
import evaluate
print(evaluate.__version__)
print(evaluate.load)
```

3. Route by task:
   - Load, discover, inspect, or choose a metric/comparison/measurement: `sub-skills/module-loading/`.
   - Compute, stream, combine, cache, distribute, or save module results: `sub-skills/module-computation/`.
   - Evaluate a model/pipeline/dataset task or run an `EvaluationSuite`: `sub-skills/evaluator-pipelines/`.
   - Create, validate, or publish a custom evaluation module: `sub-skills/hub-and-cli/`.
4. Read `references/troubleshooting.md` before running network-bound, credential-bound, backend-heavy, code-executing, or distributed/cache-sensitive workflows.
5. Run `scripts/check_evaluate_environment.py` for a safe local inspection of installed package version, optional imports, CLI availability, and known compatibility hazards.

## Core Routes

### Module Loading

Use `sub-skills/module-loading/` for:

- `evaluate.load("accuracy")`, `evaluate.load("glue", config_name="mrpc")`, local module paths, Hub/community modules, and `module_type="metric"|"comparison"|"measurement"`.
- `evaluate.list_evaluation_modules(...)` and `evaluate.inspect_evaluation_module(...)`.
- Module cards, requirements, optional dependency failures, dynamic module cache imports, and safety checks for untrusted modules such as code execution metrics.

### Module Computation

Use `sub-skills/module-computation/` for:

- `module.compute(predictions=..., references=...)`, `module.add(...)`, and `module.add_batch(...)`.
- `evaluate.combine(...)`, output key collisions, `force_prefix=True`, cache directories, distributed `num_process`/`process_id`, and `experiment_id`.
- `evaluate.save(...)`, result JSON records, and debugging input feature/shape/type validation.

### Evaluator Pipelines

Use `sub-skills/evaluator-pipelines/` for:

- `evaluate.evaluator("text-classification")` and supported task evaluators for NLP, vision, and audio.
- Dataset columns, model IDs or prebuilt pipelines, devices, label mappings, `strategy="bootstrap"`, performance metrics, and `EvaluationSuite`/`SubTask` orchestration.
- Avoiding accidental model or dataset downloads in CI or offline contexts.

### Hub And CLI

Use `sub-skills/hub-and-cli/` for:

- `evaluate-cli create`, custom module file structure, `_info`, `_compute`, optional `_download_and_prepare`, README/module cards, and generated widget caveats.
- `evaluate.push_to_hub(...)`, model-card metadata updates, Hub credentials, namespaces, organizations, and private/public Space decisions.
- CLI dependency problems such as missing `cookiecutter` or an incompatible `huggingface_hub.Repository` import.

## Shared References And Scripts

- `references/shared-api-reference.md`: public API overview that spans several routes, including loading, computing, evaluators, saving, visualization, logging, and package extras.
- `references/troubleshooting.md`: cross-cutting install/import, optional dependency, cache, offline/network, Hub, CLI, backend, and visualization failure modes.
- `references/repo-provenance.md`: source snapshot and evidence paths for deciding whether this skill is stale for a repository checkout.
- `scripts/check_evaluate_environment.py`: safe environment checker that never downloads models/datasets and never mutates Hub state.

## Important Safety Boundaries

- Treat evaluation modules as executable Python code. Do not load untrusted local or community modules unless the user accepts that risk.
- Do not run code execution metrics unless the user explicitly opts in and the environment is sandboxed.
- Do not run `evaluate-cli create`, `git clone`, Hub login, `push_to_hub`, or Space creation unless the user explicitly requests credentialed network mutation.
- Do not assume evaluator pipelines can run just because `transformers` imports; real pipeline inference needs a backend such as PyTorch, TensorFlow, or Flax and may download models or datasets.
- Do not assume every metric dependency is installed by `pip install evaluate`; module-specific `requirements.txt` files and README cards often name optional packages.
