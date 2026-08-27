---
name: openai-serving
description: "Use for vLLM OpenAI-compatible serving workflows: vllm
  serve/chat/complete/run-batch, OpenAI clients, server lifecycle, API request
  validation, batch JSONL, and client/server troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# openai-serving

Use this sub-skill when the task is about running or consuming vLLM as an OpenAI-compatible HTTP server rather than using the offline Python `LLM` API.

## Route here

- Build or explain `vllm serve` commands, including host/port, API key, CORS, frontend, logging, model identity, dtype, tensor parallelism, memory, and max context flags.
- Use `vllm chat`, `vllm complete`, OpenAI Python clients, `curl`, or batch JSONL against `/v1` endpoints.
- Diagnose client errors such as connection refused, wrong `/v1` base URL, auth mismatch, 404 model mismatch, request-schema validation, streaming expectations, and port conflicts.
- Validate server readiness with `/health`, discover model names with `/v1/models`, inspect logs, and separate server lifecycle issues from request payload issues.

## Route elsewhere

- Offline in-process inference with `vllm.LLM`, `SamplingParams`, or `LLM.chat`: use `../offline-inference/SKILL.md`.
- Deep structured outputs, tool calling, tool parsers, or reasoning schemas: use `../structured-tool-reasoning/SKILL.md`.
- Multimodal, embeddings, pooling, rerank, score, LoRA, and adapter-specific endpoint behavior: use `../modalities-adapters-pooling/SKILL.md`.
- GPU capacity planning, throughput tuning, multi-node scaling, and deployment architectures: use `../deployment-performance/SKILL.md`.

## References

- Start with `references/cli-reference.md` for `serve`, `chat`, `complete`, and `run-batch` command patterns.
- Use `references/openai-api-workflows.md` for OpenAI-compatible client payloads, endpoints, model naming, and validation checks.
- Use `references/troubleshooting.md` for symptoms, likely causes, commands to run, and routing for hardware/performance failures.

## Bundled helpers

- `scripts/serve_command_builder.py` prints a safe `vllm serve` command from common frontend and engine options.
- `scripts/openai_client_smoke.py` checks `/v1/models` and can issue a minimal chat or completion request when a user-provided server is running.

Both scripts are self-contained and require only normal Python plus the `openai` package for the smoke client. They do not start model downloads or a server unless the user runs the printed command.
