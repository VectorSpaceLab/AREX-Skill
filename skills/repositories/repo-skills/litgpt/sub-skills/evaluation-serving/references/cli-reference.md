# CLI Reference for Evaluation and Serving

This reference distills verified `litgpt evaluate` and `litgpt serve` behavior from CLI help, source signatures, tutorials, and tests. It is self-contained; do not depend on the original repository checkout at runtime.

## `litgpt evaluate`

Purpose: evaluate a LitGPT checkpoint through EleutherAI LM Evaluation Harness. It converts LitGPT checkpoint files into an HFLM-compatible output directory before running harness tasks.

```bash
litgpt evaluate CHECKPOINT_DIR \
  --tasks hellaswag,truthfulqa_mc2 \
  --out_dir eval-out \
  --batch_size 1 \
  --device cuda \
  --dtype float16 \
  --limit 10 \
  --seed 1234 \
  --save_filepath eval-out/results.json
```

Important options:

| Option | Use | Notes |
| --- | --- | --- |
| `checkpoint_dir` | LitGPT checkpoint directory or supported model name | Must contain a ready checkpoint; route layout issues to `../../checkpoint-conversion/`. |
| `--tasks` | CSV task names | If omitted by the Python API, tasks are listed and no evaluation runs; CLI task listing is normally `litgpt evaluate list`. |
| `--out_dir` | Converted checkpoint and default results directory | Defaults to `checkpoint_dir/evaluate`. |
| `--force_conversion true` | Rebuild converted HFLM files | Use after changing checkpoint contents or if stale converted files are suspected. |
| `--num_fewshot` | Few-shot examples | Pass only when the chosen task supports/needs it. |
| `--batch_size` | Positive integer, `auto`, or `auto:N` | Invalid examples such as `0`, `zero`, or `invalid` raise a batch-size validation error. |
| `--device` | `cuda`, `cuda:0`, `cpu`, etc. | Defaults to CUDA when available, otherwise CPU. |
| `--dtype` | Torch dtype string/object | Useful for memory/runtime control. |
| `--limit` | Number or fraction of task examples | Use for smoke tests to avoid large benchmark runs/downloads. |
| `--seed` | Random seed | Applied to Python random, NumPy, and torch evaluation seeds. |
| `--save_filepath` | JSON result path | Defaults to `out_dir/results.json`; parent directory should exist or be in the created `out_dir`. |
| `--access_token` | Restricted model token | Avoid embedding secrets in commands; pass through user-approved secret handling only. |

Task listing:

```bash
litgpt evaluate list
litgpt evaluate list | grep mmlu
```

Result behavior:

- The evaluator prints LM Harness result tables to stdout.
- JSON results are written to `--save_filepath`, or `out_dir/results.json` by default.
- Conversion creates Hugging Face-style evaluation files under `--out_dir`, including a `pytorch_model.bin` file used by HFLM.

## `litgpt serve`

Purpose: start a LitServe HTTP server backed by a LitGPT checkpoint. This is a long-running process that loads model weights.

```bash
litgpt serve CHECKPOINT_DIR \
  --port 8000 \
  --api_path /predict \
  --temperature 0.8 \
  --top_k 50 \
  --top_p 1.0 \
  --max_new_tokens 50
```

Important options:

| Option | Use | Notes |
| --- | --- | --- |
| `checkpoint_dir` | LitGPT checkpoint directory or supported model name | Route checkpoint readiness problems to `../../checkpoint-conversion/`. |
| `--quantize` | `bnb.nf4`, `bnb.nf4-dq`, `bnb.fp4`, `bnb.fp4-dq`, `bnb.int8` | Requires bitsandbytes-compatible environment; usually CUDA/Linux-sensitive. |
| `--precision` | Fabric precision setting | If omitted, inferred from checkpoint metadata when possible. |
| `--temperature` | Sampling randomness | Values above 1 are more random; below 1 are more deterministic. |
| `--top_k` | Top-k sampling pool | Default `50`. |
| `--top_p` | Nucleus sampling threshold | Must be between `0` and `1`; default `1.0`. |
| `--max_new_tokens` | Generation length cap | Default `50`. |
| `--devices` | Number of devices/GPUs for model distribution | Default `1`; multi-device serving may imply sequential generation unless strategy is set. |
| `--accelerator` | `auto`, `cuda`, `cpu`, `mps` | Default `auto`; CPU is safer for tiny smoke models but slow for real LLMs. |
| `--port` | HTTP port | Default `8000`; check for conflicts before starting. |
| `--stream true` | Simple endpoint streams token chunks | Response is line-oriented JSON objects with `output` fields. |
| `--openai_spec true` | Use OpenAI-compatible chat completions endpoint | Enables `/v1/chat/completions`; requires `litserve` and `jinja2`. |
| `--api_path` | Simple/custom endpoint path | Default `/predict`; OpenAI mode uses the OpenAI spec route regardless of simple prompt shape. |
| `--timeout` | Request timeout seconds | Default `30`. |
| `--generate_strategy` | `sequential` or `tensor_parallel` | `sequential` helps shard blocks across devices; `tensor_parallel` requires suitable multi-GPU setup. |
| `--access_token` | Restricted model token | Avoid exposing secrets in logs or scripts. |

Mode selection from source behavior:

- `--openai_spec true` selects `OpenAISpecLitAPI` and OpenAI-compatible request/response schema.
- Otherwise `--stream true` selects `StreamLitAPI` for streaming simple prompt responses.
- Otherwise LitGPT uses `SimpleLitAPI` with JSON payloads shaped like `{"prompt": "..."}` and responses shaped like `{"output": "..."}`.

## Optional Dependencies

| Workflow | Required optional package | Why |
| --- | --- | --- |
| `litgpt evaluate` | `lm_eval` | Task listing, evaluator, HFLM wrapper, result table formatting. |
| `litgpt serve` | `litserve` | `LitAPI`, `LitServer`, and OpenAI spec integration. |
| `litgpt serve --openai_spec true` | `jinja2` | Applies tokenizer chat templates to message lists. |
| `litgpt serve --quantize bnb.*` | `bitsandbytes` | Provides quantized linear layers/precision support. |

Use `scripts/check_optional_eval_serve_deps.py` before planning evaluation or serving in a minimal environment.
