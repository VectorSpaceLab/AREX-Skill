# Evaluation Configuration Files

Use YAML configs when a run has enough options that a command line becomes fragile, when a team needs reproducible settings, or when results should preserve the exact evaluation setup.

## Minimal Config

```yaml
model: hf
model_args:
  pretrained: gpt2
  dtype: float32

tasks:
  - hellaswag

batch_size: 1
device: cpu
limit: 5
```

Run it with:

```bash
lm-eval run --config eval.yaml
```

`limit` is suitable for testing only; remove it for real metrics.

## Config With Samples, Output, and Cache

```yaml
model: hf
model_args:
  pretrained: gpt2
  dtype: float32

tasks:
  - hellaswag

samples:
  hellaswag: [0, 1, 2]

output_path: results/gpt2-debug
log_samples: true
use_cache: cache/gpt2_responses
cache_requests: true
seed: [0, 1234, 1234, 1234]
batch_size: 1
device: cpu
```

Do not set both `samples` and `limit`; configuration validation rejects that combination.

## Config With Chat Template

```yaml
model: hf
model_args:
  pretrained: instruction-tuned-model
  dtype: float32

tasks:
  - gsm8k

apply_chat_template: true
fewshot_as_multiturn: true
system_instruction: Answer with the final result only.
gen_kwargs:
  temperature: 0
  do_sample: false

output_path: results/chat-eval
log_samples: true
batch_size: auto
device: cuda:0
```

`fewshot_as_multiturn` defaults to true when `apply_chat_template` is set. If explicitly true without chat-template formatting, validation raises an error.

## Field Reference

| Field | Type | Purpose |
| --- | --- | --- |
| `model` | string | Model backend alias such as `hf`, `vllm`, or API/local aliases registered by the package. |
| `model_args` | mapping | Constructor arguments passed to the selected backend. Backend-specific depth belongs in `model-backends`. |
| `tasks` | list or comma string | Task names, groups, YAML files, or a directory of YAML configs. |
| `num_fewshot` | int/null | Overrides default few-shot count unless a task explicitly fixes zero-shot. |
| `batch_size` | int/string | Integer, `auto`, or backend-supported auto mode. |
| `max_batch_size` | int/null | Upper bound for automatic batch selection. |
| `device` | string/null | Device forwarded to model construction. |
| `limit` | float/null | Smoke-test document limit only. |
| `samples` | mapping/string/null | Exact sample indices by task; incompatible with `limit`. |
| `use_cache` | string/null | Model-response cache prefix. |
| `cache_requests` | bool/string/mapping | Request/prompt cache behavior, including refresh/delete forms. |
| `output_path` | string/null | Directory or file location for result output. Required with sample logging/prediction-only. |
| `log_samples` | bool | Save per-sample inputs/outputs. |
| `predict_only` | bool | Save predictions and skip metric computation; implies sample logging. |
| `apply_chat_template` | bool/string | Apply default or named tokenizer chat template. |
| `system_instruction` | string/null | Adds a system instruction to prompts. |
| `fewshot_as_multiturn` | bool/null | Multi-turn few-shot formatting. |
| `include_path` | string/null | Extra directory containing task YAML files. |
| `gen_kwargs` | mapping | Generation options applied to generate-until tasks. |
| `wandb_args`, `wandb_config_args`, `hf_hub_log_args` | mapping | Tracking/upload configuration; analyze outputs through result logging guidance. |
| `seed` | int/list | One int or four seeds for Python, NumPy, torch, few-shot sampling. |
| `trust_remote_code` | bool | Allows remote code in compatible Hugging Face paths and forwards into `model_args`. |
| `confirm_run_unsafe_code` | bool | Confirms intentional execution of tasks marked unsafe. |
| `metadata` | mapping | Extra task metadata; merged with `model_args` for task processing. |

## CLI Override Rules

`EvaluatorConfig.from_cli()` loads built-in defaults, merges YAML from `--config`, then applies CLI arguments. Use that order deliberately:

```bash
lm-eval run --config production.yaml --tasks hellaswag --limit 20
```

This keeps production defaults but safely narrows a debugging run. Remove the override before reporting final results.

## Building Configs Safely

The bundled builder can write a config without importing model backends:

```bash
python scripts/build_eval_command.py \
  --write-config eval.yaml \
  --model hf \
  --model-arg pretrained=gpt2 \
  --model-arg dtype=float32 \
  --tasks hellaswag,arc_easy \
  --output-path results/gpt2 \
  --log-samples \
  --cache-requests true \
  --seed 0,1234,1234,1234
```

Review the generated YAML before a costly run, especially `output_path`, `log_samples`, `limit`, `samples`, and unsafe-code settings.
