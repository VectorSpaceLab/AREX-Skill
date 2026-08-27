---
name: offline-inference
description: "Use vLLM from Python for local/offline LLM workflows with LLM,
  SamplingParams, generate, chat, encode, embed, classify, score, output
  extraction, and safe smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Offline Inference

Use this sub-skill when the task is to run vLLM directly from Python without starting an OpenAI-compatible HTTP server. It covers `vllm.LLM`, `SamplingParams`, `LLM.generate`, `LLM.chat`, pooling entrypoints, output interpretation, prompt/chat formatting, and small user-provided-model smoke checks.

## Route Here

- Build or debug Python scripts that instantiate `LLM(model=...)` and call `generate`, `chat`, `encode`, `embed`, `classify`, or `score`.
- Convert between raw prompt completion and chat-message workflows without launching a server.
- Explain `SamplingParams` defaults and common generation controls such as `temperature`, `top_p`, `top_k`, `n`, `max_tokens`, logprobs, stop conditions, and structured output knobs.
- Interpret returned objects such as `RequestOutput`, `CompletionOutput`, `EmbeddingRequestOutput`, `ClassificationRequestOutput`, and `ScoringRequestOutput`.
- Run a deterministic short smoke check when the user provides a model identifier or local model path.

## Route Elsewhere

- OpenAI-compatible server startup, HTTP clients, endpoint lifecycle, and request authorization setup: use `../openai-serving/`.
- Deep structured JSON, tool calling, reasoning parser, or guided decoding behavior: use `../structured-tool-reasoning/`.
- Model-specific multimodal, LoRA, adapter, embedding/reranker architecture, or pooling deep dives: use `../modalities-adapters-pooling/`.
- Multi-node topology, production deployment, benchmark tuning, throughput, memory planning, or hardware sizing: use `../deployment-performance/`.

## Start Points

- For exact Python API patterns, read `references/api-reference.md`.
- For task-oriented workflows and validation commands, read `references/workflows.md`.
- For failure diagnosis and misuse patterns, read `references/troubleshooting.md`.
- For a safe script that prints a plan by default and only runs when explicitly requested with a model, use `scripts/offline_api_smoke.py`.
