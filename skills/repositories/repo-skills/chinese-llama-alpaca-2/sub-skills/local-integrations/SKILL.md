---
name: local-integrations
description: "Routes Chinese-LLaMA-Alpaca-2 llama.cpp wrappers and external
  integration notes."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# local-integrations

Use this sub-skill when the task is outside the direct HF scripts but still tied to the repo's local deployment or downstream integration examples.

## Use it when

- the user mentions llama.cpp, GGUF, `chat.sh`, or the llama.cpp completion server
- the task is about reproducing the repo's Alpaca-2 prompt format in a local runtime
- the user asks about the LangChain or privateGPT examples from this repo snapshot
- the task needs a quick explanation of why those external examples are reference-only here

## Workflow

1. Read `references/workflows.md` for llama.cpp wrapper usage and external integration notes.
2. Use `scripts/llama-cpp/chat.sh` only when a llama.cpp `main` binary and compatible model path are already available.
3. Use `scripts/llama-cpp/server_curl_example.sh` only after a llama.cpp server is already running.
4. Treat LangChain/privateGPT guidance as adaptation notes rather than a bundled runtime stack.
5. Read `references/troubleshooting.md` when an external binary, model, or third-party package is missing.

## Bundled runtime files

- `scripts/llama-cpp/chat.sh`
- `scripts/llama-cpp/server_curl_example.sh`

## What to read first

- `references/workflows.md` for the integration surfaces and prompt format
- `references/troubleshooting.md` for external binary/server/scaffold failures

## Routing notes

- Use `api-serving` for the repo's FastAPI OpenAI-compatible server.
- Use this sub-skill for llama.cpp or downstream integration notes.
- Use a dedicated RAG or LangChain skill when the task is generic framework work and no longer depends on Chinese-LLaMA-Alpaca-2 prompts or model paths.
