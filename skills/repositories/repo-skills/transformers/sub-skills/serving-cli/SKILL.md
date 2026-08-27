---
name: serving-cli
description: "Use the Transformers CLI for download, chat, local serving,
  OpenAI-compatible endpoints, server options, model warmup, continuous batching
  flags, CORS, reasoning, and safe preflight checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving CLI

Use this sub-skill when an agent needs `transformers` command-line workflows: `download`, `chat`, `serve`, local OpenAI-compatible HTTP APIs, model warmup, server options, CORS, reasoning flags, or a safe preflight before starting long-lived services.

## Route First

- Use this sub-skill for `transformers --help`, `transformers download`, `transformers chat`, `transformers serve`, `/v1/chat/completions`, `/v1/completions`, `/v1/responses`, `/v1/audio/transcriptions`, `/v1/models`, `/load_model`, and server startup diagnostics.
- Use sibling [inference-pipelines](../inference-pipelines/SKILL.md) for in-process `pipeline(...)` task selection, batching, dtype/device choices, and no-server inference.
- Use sibling [generation](../generation/SKILL.md) for `GenerationConfig`, `generate()`, streamers, decoding strategy, chat templates, and continuous batching internals outside the CLI server.
- Use sibling [tokenizers-processors](../tokenizers-processors/SKILL.md) for tokenizer/processor loading, multimodal preprocessing, chat templates, and local asset validation.
- Use sibling [training](../training/SKILL.md) for `Trainer`, `TrainingArguments`, fine-tuning, distributed training, and Hub pushing from training jobs.
- Use sibling [quantization-integrations](../quantization-integrations/SKILL.md) for bitsandbytes, GPTQ/AWQ/Quanto, Accelerate placement, and backend-specific memory reductions.
- Use sibling [model-extension](../model-extension/SKILL.md) for new architectures, custom modeling files, dynamic modules, and `trust_remote_code` review.

## Core CLI Map

The inspected package exposes the console script:

```bash
transformers --help
```

It dispatches to the CLI app at `transformers.cli.transformers:main` with commands including:

- `transformers download MODEL_ID [--cache-dir DIR] [--force-download] [--trust-remote-code]`
- `transformers chat MODEL_ID [BASE_URL] [--system-prompt TEXT] [--save-folder DIR] [generate_flag=value ...]`
- `transformers serve [MODEL_ID] [server/model/continuous-batching options]`
- `transformers env` and `transformers version` for environment reporting.

For option groups, command examples, and expected signals, use [references/cli-reference.md](references/cli-reference.md).

## Safe Preflight

Before asking an agent to start a server, run the bundled dry-run helper:

```bash
python sub-skills/serving-cli/scripts/cli_preflight.py --check-serving --check-clients
```

Expected success signal: `OK serving CLI preflight passed` with imported modules and optional package availability. Expected failure signal: non-zero exit with `ERROR` lines naming missing hard requirements or requested extras. The script does not download models, bind ports, or start `uvicorn` unless a future caller edits it; by default it only imports modules, checks optional packages, validates argument combinations, and optionally probes a health URL.

Use `--port 8000` to test whether a local port appears available before starting `transformers serve`. Use `--base-url http://localhost:8000 --probe-health` only when a server is expected to already be running.

## Starting A Server Safely

Default `transformers serve` starts a long-lived FastAPI/Uvicorn server on `localhost:8000`. Do not launch it by default in automated verification; prefer preflight and command construction unless the user explicitly asks to run a service.

Minimal command:

```bash
transformers serve --host localhost --port 8000 --log-level info
```

Common production-like local command:

```bash
transformers serve Qwen/Qwen2.5-0.5B-Instruct \
  --host localhost \
  --port 8000 \
  --dtype auto \
  --device auto \
  --model-timeout 300
```

Decision points:

- Add positional `MODEL_ID` to force one preloaded model and prevent idle unload for that model.
- Omit positional `MODEL_ID` for on-demand model loading driven by request bodies.
- Keep `--trust-remote-code` off unless custom repository code was reviewed.
- Use `--enable-cors` only for browser-based clients that need it; it enables permissive CORS.
- Use `--model-timeout SECONDS` to unload idle on-demand models; it is ignored when a force model is provided.
- Use `--default-seed N` when reproducibility matters and the backend supports deterministic behavior.

Full serving workflows are in [references/serving-workflows.md](references/serving-workflows.md).

## Chat CLI

`transformers chat` is an interactive client for an already running `transformers serve` server. It calls `/load_model` to show model download/loading progress, then streams chat completions through the server.

```bash
transformers chat Qwen/Qwen2.5-0.5B-Instruct http://localhost:8000 max_new_tokens=128 do_sample=False
```

Inside the interactive prompt:

- `!help` prints commands.
- `!status` prints model and generation settings.
- `!clear` resets conversation history.
- `!set temperature=0.7 max_new_tokens=256` updates generation settings.
- `!save NAME` saves conversation and settings.
- `!exit` ends the chat client.

If chat fails immediately, verify that the server is reachable at the positional `BASE_URL`, `/health` returns a response, and `/load_model` can stream a `ready` event for the chosen model.

## OpenAI-Compatible APIs

`transformers serve` implements local endpoints compatible with common OpenAI client patterns:

- `POST /v1/chat/completions` for chat, multimodal messages, streaming, tools where supported, and reasoning fields.
- `POST /v1/completions` for legacy prompt completion and `choices[].text` outputs.
- `POST /v1/responses` for Responses API-style text, image, audio, video, multi-turn, and streaming workflows.
- `POST /v1/audio/transcriptions` for multipart audio transcription.
- `GET /v1/models` for locally cached generative model discovery.
- `POST /load_model` for SSE model warmup and download/loading progress.
- `GET /health` for server liveness.

Use [references/openai-api.md](references/openai-api.md) for request bodies, Python client snippets, streaming expectations, unsupported-field behavior, and response checks.

## Continuous Batching And Optimizations

Enable continuous batching only after confirming backend and model compatibility:

```bash
transformers serve \
  --continuous-batching \
  --attn-implementation sdpa \
  --dtype bfloat16 \
  --cb-block-size 16 \
  --cb-max-batch-tokens 4096
```

Important constraints:

- `--compile` improves some decode loops but is documented as incompatible with continuous batching.
- `--quantization bnb-4bit` and `--quantization bnb-8bit` request runtime bitsandbytes quantization; pre-quantized models may not need a server flag.
- `--attn-implementation flash_attention_2` or `sdpa` must match installed kernels and hardware.
- `--cb-use-cuda-graph`, `--cb-num-blocks`, `--cb-max-memory-percent`, and related KV cache sizing flags are performance tuning knobs, not correctness fixes.

For deeper generation and continuous batching concepts, route to [generation](../generation/SKILL.md). For quantization package choices, route to [quantization-integrations](../quantization-integrations/SKILL.md).

## Optional Dependency Boundary

A minimal Transformers import is not enough for all CLI workflows. Known boundaries:

- CLI app import can fail if base CLI dependencies such as `requests` are missing, because `transformers chat` imports HTTP clients.
- `transformers serve` requires serving extras such as `fastapi`, `uvicorn`, `pydantic`, and `openai`; install with `pip install "transformers[serving]"` when available.
- `transformers chat` uses `requests`, `httpx`, `huggingface_hub`, optional `rich`, and server-side `/load_model`.
- Model-backed serving requires backend packages such as `torch`; PyTorch-dependent classes raise optional dependency `ImportError` when torch is absent.
- Audio and multimodal serving may need additional packages for audio/video/image decoding beyond the base serving stack.

Troubleshooting paths and minimal install suggestions are in [references/troubleshooting.md](references/troubleshooting.md).

## Fast Validation Checklist

1. Run `python sub-skills/serving-cli/scripts/cli_preflight.py --check-serving --check-clients --port 8000`.
2. Check `transformers --help` only after `requests` and Typer-related CLI dependencies import successfully.
3. Construct the intended `transformers serve` command without running it.
4. Confirm port availability, host binding, CORS need, model source, `trust_remote_code`, dtype/device, and timeout policy.
5. If a server is already running, probe `GET /health` and optionally `GET /v1/models` before sending generation requests.
6. Warm up with `POST /load_model` only when network/model downloads and backend memory are acceptable.
7. Send a tiny non-streaming request before enabling streaming, continuous batching, quantization, or browser clients.

## Evidence Base

This sub-skill distills Transformers 5.13.0.dev0 behavior from CLI entrypoints, chat/download/serve command implementations, serving handlers, serve CLI docs, conversation docs, optimization docs, and CLI tests. Runtime guidance is self-contained and does not require opening source repository files.
