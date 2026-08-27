---
name: evaluation-serving
description: "Evaluate LitGPT checkpoints with LM Evaluation Harness and serve
  LitGPT models through LitServe, including optional dependency checks, endpoint
  modes, result files, and safe preflight planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LitGPT Evaluation and Serving

Use this sub-skill when an agent needs to run or plan `litgpt evaluate`, list LM Evaluation Harness tasks, interpret evaluation result files, start `litgpt serve`, or build Simple/Streaming/OpenAI-compatible request examples.

## Route First

- For checkpoint download, conversion, validation, LoRA merge, tokenizer/config layout, or `litgpt validate`, use `../checkpoint-conversion/` first.
- For local one-shot generation, chat, prompt styles, `LLM.load`, `LLM.generate`, or non-HTTP streaming, use `../inference-chat/`.
- For finetuning, pretraining, dataset formatting, recipe adaptation, or training-time eval settings, use `../training-data/`.

## Safe Workflow

1. Confirm the checkpoint is ready before any long operation; if layout is uncertain, route to `../checkpoint-conversion/`.
2. Run the bundled preflight checker instead of starting services or benchmarks:
   `python scripts/check_optional_eval_serve_deps.py --checkpoint-dir CHECKPOINT_DIR --mode both`.
3. For evaluation, install/confirm `lm_eval`, choose a small `--tasks` set, set `--limit` for smoke runs, and choose an explicit `--save_filepath` when results must be collected.
4. For serving, install/confirm `litserve`; also confirm `jinja2` and tokenizer chat-template readiness when using `--openai_spec true`.
5. Build request examples before starting a server:
   `python scripts/build_curl_examples.py --port 8000 --api-path /predict --mode simple` or `--mode openai --api-path /v1/chat/completions`.
6. Treat `litgpt serve` and full LM Harness runs as long-running/manual steps unless the user explicitly approves a bounded run.

## Quick Commands

- List tasks: `litgpt evaluate list`.
- Smoke evaluate: `litgpt evaluate CHECKPOINT_DIR --tasks hellaswag --batch_size 1 --limit 10 --out_dir eval-out --save_filepath eval-out/results.json`.
- Force reconversion after checkpoint changes: add `--force_conversion true`.
- Serve simple JSON API: `litgpt serve CHECKPOINT_DIR --port 8000 --api_path /predict`.
- Serve streaming simple API: `litgpt serve CHECKPOINT_DIR --stream true --api_path /predict`.
- Serve OpenAI-compatible API: `litgpt serve CHECKPOINT_DIR --openai_spec true --port 8000`.

## References

- `references/cli-reference.md` summarizes `litgpt evaluate` and `litgpt serve` options.
- `references/evaluation-recipes.md` covers LM Evaluation Harness task listing, conversion behavior, limits, seeds, and result files.
- `references/deployment-recipes.md` covers LitServe Simple, Stream, and OpenAI-compatible endpoints.
- `references/troubleshooting.md` maps common symptoms to safe fixes.
- `scripts/check_optional_eval_serve_deps.py` checks optional imports, batch-size syntax, port availability, and checkpoint readiness hints.
- `scripts/build_curl_examples.py` generates curl examples for simple, streaming, and OpenAI-compatible requests.
