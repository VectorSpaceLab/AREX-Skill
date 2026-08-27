---
name: task-authoring
description: "Guide for authoring and debugging lmms-eval task YAMLs, utils.py
  formatters, metrics, groups, tags, and request-shape contracts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# task-authoring

Use this route when the user wants to add or fix a benchmark task, adjust task YAMLs, or debug how lmms-eval turns a dataset document into a model request and score.
It is the home for YAML structure, formatter functions, `process_results`, metric wiring, and request-shape validation.

## Read first

- `../../references/task-authoring.md`
- `../../references/api-reference.md`
- `../../references/troubleshooting.md`

## What this route covers

- Task YAML structure, `include` reuse, and split selection.
- `doc_to_messages`, `doc_to_text`, `doc_to_visual`, and `doc_to_target` contracts.
- `output_type` selection for `generate_until`, `loglikelihood`, and multi-round flows.
- `process_results` and `metric_list` wiring.
- Task grouping, tagging, and reasoning-tag overrides.
- Request-shape expectations for chat and simple models.

## Typical workflow

1. Confirm the task is already registered or find the right task directory to update.
2. Choose the correct output type and formatter pair for the model family.
3. Keep `process_results` and `metric_list` aligned by key name and metric direction.
4. Use task inheritance or `include` for shared YAML fragments.
5. Compare the task to the request-shape table in `api-reference.md` before debugging the model.
6. Run the task registry smoke to confirm the task is visible and loadable.

## Helpful commands

```bash
lmms-eval tasks list
lmms-eval tasks groups
lmms-eval tasks subtasks
```

## Bundled scripts

- `../../scripts/task_registry_smoke.py` — inspect the built-in task registry and optionally load one task.
- `../../scripts/task_yaml_audit.py` — audit task YAML parseability and key presence.
- `../../scripts/task_input_capture.py` — capture built request-boundary summaries for a task without running model inference; prefer small or cached tasks because it still constructs task requests.

## Cross-route handoff

- Send backend class selection, `is_simple`, and video/media decode questions to `model-backends`.
- Send direct CLI flags, caching, and reasoning-tag questions to `cli-and-workflows`.
- Send server-side queue, client, or MCP questions to `service-ops`.

## Common failure modes

- YAML indentation or `include` errors.
- `doc_to_messages` exists but the model receives the wrong request tuple shape.
- `process_results` returns a metric key that is not in `metric_list`.
- Dataset split or media extraction settings point at the wrong field.
- Reasoning-tag overrides make prompt-scoring differ from the expected clean output.

Use the registry smoke and the API reference before opening the source tree for a task-shaped bug.
