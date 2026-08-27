# Troubleshooting Evaluation Runs

## Missing or Empty Tasks

Symptoms:

- CLI validation fails with a missing task.
- Python raises `Tasks not found: ...` or `No tasks specified, or no tasks found`.

Checks:

```bash
lm-eval ls tasks | grep hellaswag
lm-eval validate --tasks hellaswag
lm-eval ls tasks --include_path ./task_yamls
```

Fixes:

- Use the exact registered task, group, subtask, or tag name.
- Pass comma-separated or space-separated task names, not a shell-expanded malformed string.
- Add `--include_path` or `TaskManager(include_path=...)` for external YAML tasks.
- For authoring or repairing task YAML, route to `task-authoring`.

## `log_samples` or `predict_only` Without Output Path

Symptoms:

- Configuration validation raises: `Specify --output_path if providing --log_samples or --predict_only`.

Fix:

```bash
lm-eval run \
  --model hf --model_args pretrained=gpt2 \
  --tasks hellaswag \
  --output_path results/gpt2-debug \
  --log_samples
```

`--predict_only` implies sample logging, so it also needs `--output_path`.

## `samples` Conflicts With `limit`

Symptoms:

- CLI/config/Python validation raises that `samples` and `limit` are mutually exclusive.

Fix:

- Use `--limit 5` for quick smoke tests across the first documents.
- Use `--samples '{"task": [0, 1]}'` for exact document debugging.
- Do not combine them.

The bundled command builder rejects this conflict before producing a command.

## Limit Used for Real Metrics

`--limit` and `limit=` are for testing only. Limited runs are useful for checking model loading, prompt rendering, output paths, and logging, but metrics should not be cited as benchmark results.

Before a final run:

- Remove `--limit` / `limit:`.
- Remove debugging-only `--write_out` if not needed.
- Keep seeds, model args, task names, and output path reproducible.

## Chat Template and Few-Shot Misuse

Symptoms:

- Instruct/chat model gives poor outputs.
- Evaluator warns that model args look chat-like but `apply_chat_template` is not set.
- Validation fails because `fewshot_as_multiturn=True` was set without `apply_chat_template`.

Fixes:

```bash
lm-eval run \
  --model hf --model_args pretrained=instruction-tuned-model \
  --tasks gsm8k \
  --apply_chat_template \
  --fewshot_as_multiturn true
```

- Use `--apply_chat_template` for instruction/chat tuned models when the backend tokenizer has an appropriate template.
- Only use `--fewshot_as_multiturn` with chat-template formatting.
- For model-specific template support or backend-specific arguments, route to `model-backends`.

## Request Cache Refresh or Delete

`--cache_requests` controls cached preprocessing/request construction, not the model-response cache from `--use_cache`.

Patterns:

```bash
lm-eval run ... --cache_requests true
lm-eval run ... --cache_requests refresh
lm-eval run ... --cache_requests delete
```

Use `refresh` after changing task prompt construction, metadata, task YAML, or dataset processing code. Use `delete` when cache state may be corrupt or stale.

## Model Response Cache Surprises

`--use_cache cache/prefix` creates per-rank SQLite cache files internally. If a run appears to reuse old model outputs, change the prefix or remove old cache files before rerunning. Do not confuse this with `--cache_requests`.

## Unsafe Code Confirmation

Some tasks may execute arbitrary Python or require explicit unsafe-code confirmation.

CLI:

```bash
lm-eval run ... --confirm_run_unsafe_code
```

Python:

```python
lm_eval.simple_evaluate(..., confirm_run_unsafe_code=True)
```

Only set this after reviewing the task source/config and accepting the execution risk. For task-level safety review or authoring changes, route to `task-authoring` or `decontamination-maintenance` depending on the workflow.

## Optional Backend Dependency Missing

Symptoms:

- Import errors for `torch`, `transformers`, `vllm`, API clients, or backend-specific packages.
- Model registry errors after selecting a backend whose extra was not installed.

Fixes:

- The base package intentionally excludes heavy optional backends.
- Install only the needed extra for the selected backend, such as an HF, vLLM, or API extra.
- Import `lm_eval.models` before registry introspection scripts that expect all model aliases to be populated.
- Route backend installation, device placement, and backend-specific `model_args` debugging to `model-backends`.

## Debugging Prompt Rendering

Use a tiny debug run:

```bash
LMEVAL_LOG_LEVEL=DEBUG lm-eval run \
  --model hf --model_args pretrained=gpt2,dtype=float32 \
  --tasks hellaswag \
  --device cpu \
  --batch_size 1 \
  --limit 2 \
  --write_out \
  --show_config
```

If prompt content is wrong, determine whether the issue is task YAML/prompt construction (`task-authoring`), chat template/model tokenizer behavior (`model-backends`), or run-flag selection (`evaluation-runs`).
