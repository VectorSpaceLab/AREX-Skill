# CLI reference

The top-level command is `lmms-eval`. The dispatcher supports both modern subcommands and the legacy flat-argument form.

## Entry points

| Command | Purpose |
| --- | --- |
| `lmms-eval eval` | Run an evaluation or launch the interactive wizard when no args are given |
| `lmms-eval tasks` | List tasks, groups, subtasks, or tags |
| `lmms-eval models` | List registered model backends and aliases |
| `lmms-eval serve` | Start the HTTP evaluation server |
| `lmms-eval ui` | Launch the browser UI |
| `lmms-eval mcp` | Start the MCP server |
| `lmms-eval power` | Sample-size / power analysis |
| `lmms-eval version` | Print version and environment info |
| `lmms-eval tui` | Launch the terminal UI |

Legacy still works:

```bash
lmms-eval --model qwen2_5_vl --tasks mme --batch_size 1 --limit 8
```

## Evaluation flags worth knowing

| Flag | Meaning |
| --- | --- |
| `--config PATH` | YAML-driven run config; CLI overrides YAML |
| `--model` | Model backend name |
| `--model_args` | Comma-separated constructor args for the backend |
| `--tasks` | Task or group names; `list` shows registered names |
| `--num_fewshot` | Number of few-shot examples |
| `--batch_size` | Batch size (`1`, `auto`, or `auto:N` in CLI help) |
| `--limit` | Small smoke count or fraction of each task |
| `--output_path` | Result/output directory or JSONL path |
| `--log_samples` | Save per-sample outputs and prompts |
| `--use_cache` | Enable the layered response cache |
| `--cache_requests` | `true`, `refresh`, or `delete` for request caching |
| `--reasoning_tags` | Enable/disable or customize `<think>` stripping |
| `--apply_chat_template` | Apply a chat template to prompts |
| `--fewshot_as_multiturn` | Treat few-shot examples as a multi-turn conversation |
| `--predict_only` | Generate outputs without metrics |
| `--check_integrity` | Run task integrity checks |
| `--write_out` | Print the first prompt and target for each task |
| `--seed` | Seed Python, NumPy, and PyTorch |
| `--device` | Target device (for local models) |
| `--force_simple` | Force simple model resolution when a dual backend exists |
| `--max_tokens` | Older CLI alias used by tests; map carefully when inspecting legacy workflows |

## Browsing and debug commands

```bash
lmms-eval tasks list
lmms-eval tasks groups
lmms-eval tasks subtasks
lmms-eval tasks tags
lmms-eval models --aliases
lmms-eval version
lmms-eval power --effect-size 0.03 --tasks mme
```

## Service commands

```bash
lmms-eval serve --host 0.0.0.0 --port 8000
lmms-eval ui --port 8000
lmms-eval mcp --transport stdio
lmms-eval tui
```

## Quick smoke recipes

- Direct eval smoke: `--limit 5` or `--limit 8` with a tiny task.
- Registry smoke: `tasks list` and `models --aliases`.
- Config smoke: `--config <yaml>` with a CLI override such as `--limit 5`.
- Cache smoke: run the same deterministic command twice with `--use_cache`.

## Common CLI mistakes

- Using `--model_args` values that belong in YAML or vice versa.
- Forgetting `--log_samples` when you expect prompt/output files.
- Treating `--limit` as a full benchmark setting; it is only for smoke/debug.
- Mixing `--reasoning_tags` and task-level `reasoning_tags` without checking precedence.
- Expecting `--tasks` to accept unknown names; use `lmms-eval tasks list` first.

For the exact parsing behavior and current default values, prefer the installed package help and the repository tests over memory.
