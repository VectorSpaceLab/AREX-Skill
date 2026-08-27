---
name: module-loading
description: "Discover, inspect, and load Hugging Face Evaluate metrics,
  comparisons, measurements, local module scripts, built-in modules, and
  Hub/community modules."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Module Loading

Use this sub-skill when an agent needs to find or instantiate an Evaluate evaluation module before computing with it. Route actual `compute`, `add`, `add_batch`, cache-file, or distributed result aggregation work to `../module-computation/`; route evaluator pipeline usage to `../evaluator-pipelines/`; route module creation, packaging, CLI, or Hub publishing workflows to `../hub-and-cli/`.

## Fast Path

1. Pick the module source: built-in/canonical name such as `accuracy`, community Hub repo such as `lvwerra/element_count`, or a local script/directory.
2. Pick the module type when it is not obvious: `metric`, `comparison`, or `measurement`.
3. Inspect available modules or module source before loading when the name, card, dependencies, or safety profile is uncertain.
4. Load with `evaluate.load(path, module_type=..., config_name=..., revision=...)` and inspect `.features`, `.description`, `.inputs_description`, `.citation`, and related info attributes before computing.
5. Treat module code as executable Python. Avoid untrusted local/community modules and never run `code_eval` unless the user explicitly accepts sandboxed code execution.

## Main Workflows

- `references/loading-workflows.md` covers `evaluate.load`, `list_evaluation_modules`, `inspect_evaluation_module`, local paths, `config_name`, `revision`, dynamic module cache behavior, and safe local smoke checks.
- `references/module-catalog.md` summarizes built-in module types, representative metrics/comparisons/measurements, module card fields, requirements files, and safety notes.
- `references/troubleshooting.md` covers wrong `module_type`, missing paths, optional dependency `ImportError`, Hub/network/revision issues, dynamic module cache problems, and `code_eval` restrictions.
- `scripts/local_module_smoke.py` creates a tiny deterministic local metric and verifies that `evaluate.load()` can import and compute from the local directory without Hub access.

## Canonical Calls

```python
import evaluate

metric = evaluate.load("accuracy")
comparison = evaluate.load("exact_match", module_type="comparison")
measurement = evaluate.load("word_length", module_type="measurement")
community = evaluate.load("lvwerra/element_count", module_type="measurement")
glue_mrpc = evaluate.load("glue", config_name="mrpc")
```

Use `evaluate.list_evaluation_modules(module_type="metric", include_community=False, with_details=True)` to discover Hub modules and `evaluate.inspect_evaluation_module("accuracy", local_path="./accuracy_inspect")` to copy a module script for inspection or modification.

## Safety And Routing

- Loading may download and import Python code from local files or the Hub; inspect unknown modules before execution.
- Some modules need optional packages listed in their `requirements.txt`; install only user-approved dependencies in the active environment.
- `metrics/code_eval` executes candidate code via `metrics/code_eval/execute.py` and requires `HF_ALLOW_CODE_EVAL=1`; treat it as unsafe unless sandboxed.
- After a module is loaded, use `../module-computation/` for input batching, compute arguments, distributed settings, or result interpretation.
