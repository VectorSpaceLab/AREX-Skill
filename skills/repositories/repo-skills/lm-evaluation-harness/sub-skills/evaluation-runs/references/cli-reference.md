# CLI Reference for Evaluation Runs

`lm-eval` and `lm_eval` expose the evaluation harness through the same console entry point. Current releases support subcommands:

```bash
lm-eval run ...
lm-eval ls tasks
lm-eval validate --tasks hellaswag,arc_easy
```

Legacy invocations that omit `run` still route to the run command, but generated commands should include `run` for clarity.

## Minimal Run

```bash
lm-eval run \
  --model hf \
  --model_args pretrained=gpt2,dtype=float32 \
  --tasks hellaswag \
  --device cpu \
  --batch_size 1 \
  --limit 5
```

Use `--limit` only for smoke tests and debugging. Do not report benchmark metrics from limited runs.

## Config-Backed Run

```bash
lm-eval run --config eval.yaml
```

CLI flags override values loaded from `--config`, so this pattern is useful for shared defaults plus one-off task or limit changes:

```bash
lm-eval run --config eval.yaml --tasks arc_easy --limit 10
```

## Flag Catalog

| Need | Flags | Notes |
| --- | --- | --- |
| Model selection | `--model`, `--model_args` | Model backends may require optional extras. Route backend-specific dependency/install issues to `model-backends`. |
| Task selection | `--tasks`, `--include_path` | Tasks accept space-separated or comma-separated names. Use `lm-eval ls tasks` and `lm-eval validate`. |
| Few-shot control | `--num_fewshot` | Overrides task defaults except tasks that explicitly fix zero-shot. |
| Batching/device | `--batch_size`, `--max_batch_size`, `--device` | `--batch_size auto` and `auto:N` are supported by applicable model backends. |
| Generation | `--gen_kwargs` | Values are parsed as literals; for non-greedy decoding, ensure options such as `do_sample=True` are intentional. |
| Output | `--output_path`, `--log_samples`, `--predict_only` | `--log_samples` and `--predict_only` require `--output_path`; `--predict_only` implies sample logging. |
| Response cache | `--use_cache` | Path prefix for model-response SQLite caches; per-rank suffixes are added internally. |
| Request cache | `--cache_requests` | Accepts bare flag/`true`, `refresh`, or `delete`; affects preprocessed prompt/request cache. |
| Debugging | `--write_out`, `--show_config`, `LMEVAL_LOG_LEVEL=DEBUG` | Prefer short `--limit` or `--samples` smoke runs before full inference. |
| Chat formatting | `--apply_chat_template`, `--system_instruction`, `--fewshot_as_multiturn` | `--fewshot_as_multiturn` requires `--apply_chat_template` when explicitly true. |
| Reproducibility | `--seed` | Single int applies to all seeds; four comma-separated values map to Python, NumPy, torch, fewshot. Use `None` to skip a seed. |
| Security | `--trust_remote_code`, `--confirm_run_unsafe_code` | Only set after explicitly accepting remote dataset/model code or unsafe task code risks. |
| Tracking | `--wandb_args`, `--wandb_config_args`, `--hf_hub_log_args`, `--metadata` | Result-upload and sample-upload behavior belongs with result logging; task metadata may be required by some task families. |

## Listing and Validation

```bash
lm-eval ls tasks
lm-eval ls groups
lm-eval ls subtasks
lm-eval ls tags
lm-eval validate --tasks hellaswag,arc_easy
lm-eval validate --tasks custom_task --include_path ./task_yamls
```

`ls` is for discovery. `validate` checks task existence/configuration before a run. If a task is missing, check spelling, group vs subtask names, and whether custom YAMLs require `--include_path`.

## Samples vs Limit

`--samples` selects exact document indices and is mutually exclusive with `--limit`.

```bash
lm-eval run \
  --model hf --model_args pretrained=gpt2 \
  --tasks hellaswag \
  --samples '{"hellaswag": [0, 1, 2]}' \
  --output_path results/samples --log_samples
```

Use `--samples` for deterministic debugging of specific documents. Use `--limit` for quick end-to-end smoke tests.

## Chat Template Runs

```bash
lm-eval run \
  --model hf \
  --model_args pretrained=instruction-tuned-model,dtype=float32 \
  --tasks gsm8k \
  --apply_chat_template \
  --fewshot_as_multiturn true \
  --system_instruction "Answer concisely." \
  --gen_kwargs temperature=0 'stop=["\n\n"]'
```

If an instruct/chat model is used without chat-template formatting, the evaluator warns that `apply_chat_template` may be needed. Do not turn on multi-turn few-shot formatting without chat-template formatting.

## Debug Command Pattern

```bash
LMEVAL_LOG_LEVEL=DEBUG lm-eval run \
  --model hf \
  --model_args pretrained=gpt2,dtype=float32 \
  --tasks hellaswag \
  --device cpu \
  --batch_size 1 \
  --limit 2 \
  --write_out \
  --show_config
```

This pattern checks prompt rendering and configuration without committing to a full benchmark run.
