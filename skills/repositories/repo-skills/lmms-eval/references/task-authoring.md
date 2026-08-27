# Task authoring

This reference covers the YAML/config side of lmms-eval: task discovery, input formatting, metric wiring, and prompt/debug workflows.

## Discovery and loading

- Tasks live under `lmms_eval/tasks/` and auto-register from YAML at startup.
- `TaskManager(verbosity='INFO', include_path=None, include_defaults=True, model_name=None)` indexes tasks, groups, and tags.
- `get_task_dict(task_name_list, task_manager=None, task_type='simple')` loads task objects when an evaluation actually needs the dataset.

## YAML schema highlights

| Field | Purpose |
| --- | --- |
| `task` | Task id used by the CLI and registry |
| `group` / `tag` | Grouping or collection names |
| `include` | Reuse another YAML as a template |
| `dataset_path` / `dataset_name` | Hugging Face dataset location |
| `dataset_kwargs` | Extra loader args such as `token` or `cache_dir` |
| `test_split`, `validation_split`, `training_split`, `fewshot_split` | Split selection |
| `doc_to_messages` | Preferred chat-model formatter |
| `doc_to_text` | Legacy text formatter |
| `doc_to_visual` | Visual extractor for simple models |
| `doc_to_target` | Gold-answer extractor |
| `process_results` | Per-sample scoring hook |
| `metric_list` | Metric names, aggregation, and direction |
| `generation_kwargs` | Default generation settings |
| `lmms_eval_specific_kwargs` | Per-model prompt variants |
| `reasoning_tags` | Task-level override for `<think>` stripping |
| `metadata.version` | Staleness/version marker |

## Current request shapes

The current evaluator/tests expect these tuple layouts:

| Request type | Tuple shape |
| --- | --- |
| `generate_until` with simple models | `(ctx, gen_kwargs, doc_to_visual, doc_id, task, split)` |
| `generate_until` with chat/message models | `(ctx, doc_to_messages, gen_kwargs, doc_id, task, split)` |
| `loglikelihood` | `(ctx, doc_to_target, doc_to_visual, doc_id, task, split)` |
| `generate_until_multi_round` / `generate_until_agentic` | `(ctx, gen_kwargs, doc_to_visual, doc_to_text, doc_id, task, split)` |

If you are debugging a task, always check the tuple shape before blaming the model.

## Common task patterns

| Pattern | Example tasks | What to notice |
| --- | --- | --- |
| Basic image QA | `mme`, `ai2d`, `scienceqa` | Simple prompts, metric aggregation, `generate_until` |
| Chat-style multimodal | `mmmu_val` | `doc_to_messages`, prompt variants, `include` template reuse |
| Video tasks | `videomme`, `longvideobench` | `cluster_key`, media resolution, video-specific prompt text |
| Audio tasks | `openhermes`, `song_describer` | Audio extractors and provider-specific dependencies |
| Region/box tasks | `refcoco+`, `screenspot`, `point_*` families | Structured outputs and exact formatting |
| Grouped collections | `jmmmu`, `mathvista_testmini` | Nested groups and aggregated metrics |

## Metrics and scoring

- `process_results(doc, results)` returns a dict of metric inputs.
- `metric_list` names must match the keys returned by `process_results` or a registered metric name.
- `aggregation` controls the final task score aggregation.
- `higher_is_better` should match the real metric direction.

Task-side helpers frequently use:

- exact match / string normalization
- MCQ extraction
- numeric parsing
- LLM-as-judge or verifier pipelines for harder tasks

## Debugging a task

1. Confirm the task is registered via `lmms-eval tasks list`.
2. Inspect the parsed YAML and the `include` chain.
3. Check the formatter used by the selected model family.
4. Verify `process_results` returns the keys listed in `metric_list`.
5. Smoke the task with `--limit 5` or inspect the prompt stability tests if the prompt changed.

## Common task failures

- `Unknown keys in config file` → YAML typo or stale field.
- `doc_to_messages` present but the model expects `doc_to_text`/`doc_to_visual`.
- `process_results` emits a metric key that `metric_list` never references.
- `generate_until_agentic requires callable doc_to_text` → the task should supply a callable text formatter.
- `doc_to_visual` returns a single object instead of a list.
- Dataset loader issues from missing `token`, `cache_dir`, split name, or media path settings.

Use the bundled `scripts/task_registry_smoke.py` and `scripts/task_yaml_audit.py` before opening the source tree for a new task fix.
