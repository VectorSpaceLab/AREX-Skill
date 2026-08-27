# Evaluation and Serving Troubleshooting

Use this matrix to diagnose LitGPT evaluation and serving failures without starting new long-running jobs by default.

## Evaluation Symptoms

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `ModuleNotFoundError: lm_eval` or import error from `lm_eval` | LM Evaluation Harness is not installed | Install/confirm `lm_eval` in the active environment, then rerun preflight. |
| `batch_size must be a positive integer, 'auto', or in the format 'auto:N'.` | `--batch_size` was `0`, negative, or a string like `zero`/`invalid` | Use `--batch_size 1` for a minimal run, or `--batch_size auto` / `auto:N`. |
| Evaluation runs conversion again or uses stale files | `out_dir` is missing converted files or checkpoint changed | Use `--force_conversion true` after checkpoint changes. |
| HFLM cannot load converted model | Checkpoint layout or conversion output is incomplete | Route to `../../checkpoint-conversion/`, then retry evaluation conversion. |
| Task listing works but evaluation downloads a lot | LM Harness task datasets are not cached | Use `--limit`, reduce tasks, and ask before full benchmark downloads. |
| Results file missing | `--save_filepath` path was wrong or run failed before result writing | Use explicit `--out_dir` and `--save_filepath`; check stdout/stderr before rerun. |
| CPU run is extremely slow | Real benchmark/model is too large for CPU | Switch to CUDA/MPS if available or keep only tiny smoke tasks/limits. |

## Serving Symptoms

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `ModuleNotFoundError: litserve` or import error from LitServe classes | Serving optional dependency is missing | Install/confirm `litserve`; run preflight before server startup. |
| Server hangs at startup | Model loading/distribution is long-running | Treat as expected for large checkpoints; set user expectations and avoid unapproved waits. |
| Port bind failure or address already in use | Another process is using `--port` | Run the preflight port check or choose a different port. |
| `ModuleNotFoundError: jinja2` in OpenAI mode | OpenAI-compatible mode needs chat template rendering | Install/confirm `jinja2` or use simple `/predict` mode instead. |
| `tokenizer_config.json` not found in OpenAI mode | Checkpoint lacks tokenizer config beside model files | Route to `../../checkpoint-conversion/` to repair/download tokenizer files. |
| OpenAI client gets schema errors on `/predict` | Sent `messages` to simple prompt API | Use `{"prompt":"..."}` for `/predict`, or start with `--openai_spec true` and use `/v1/chat/completions`. |
| Simple client gets schema errors on `/v1/chat/completions` | Sent `prompt` to OpenAI-compatible API | Use `messages` array with role/content objects. |
| Streaming parser sees unexpected format | Confused simple streaming with OpenAI SSE streaming | Simple stream yields JSON chunks with `output`; OpenAI stream yields `data:` chunks with `choices[0].delta.content`. |
| Quantized serving fails on import/backend | `bitsandbytes` missing or incompatible | Install compatible bitsandbytes/backend, or remove `--quantize bnb.*`. |
| Multi-GPU strategy fails | Device count/backend does not support requested strategy | Try `--devices 1`, `--generate_strategy sequential`, or route environment/hardware planning to the root troubleshooting flow. |
| Request times out | Generation is slow, model is too large, or `--timeout` too low | Increase `--timeout`, reduce `--max_new_tokens`, reduce load, or use a smaller model. |

## Preflight Commands

Evaluation only:

```bash
python scripts/check_optional_eval_serve_deps.py \
  --mode evaluate \
  --checkpoint-dir CHECKPOINT_DIR \
  --batch-size 1
```

Serving only:

```bash
python scripts/check_optional_eval_serve_deps.py \
  --mode serve \
  --checkpoint-dir CHECKPOINT_DIR \
  --port 8000 \
  --openai-spec
```

Curl planning:

```bash
python scripts/build_curl_examples.py --mode simple --api-path /predict
python scripts/build_curl_examples.py --mode openai --api-path /v1/chat/completions
```

## Escalate or Route

- Route checkpoint file layout, model config, tokenizer files, and checkpoint conversion to `../../checkpoint-conversion/`.
- Route local prompt generation and Python `LLM` usage to `../../inference-chat/`.
- Route training outputs, LoRA output selection, and data issues to `../../training-data/`.
- Ask for explicit user approval before full benchmarks, downloads, public server exposure, or long-running service management.
