---
name: serving-and-cli
description: "Operate Mellea 0.8.0.dev0's m CLI and OpenAI-compatible server
  safely, including serving, routing, response schemas, streaming,
  decomposition, migration, evaluation routing, and bounded adapter commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving and CLI

Use this route for the `m` entry point, `m serve`,
`POST /v1/chat/completions`, `GET /health`, OpenAI-compatible clients, model
routing, response formats, SSE streaming, `m decompose`, `m fix`, or the
bounded CLI aspects of `m alora` and `m eval`. The operating contract is for
Mellea `0.8.0.dev0` and Python 3.11+.

## Route the task

1. Run the safe bundled checker before invoking a side-effectful command:
   `python scripts/check_cli_surface.py --mode static`. To render installed
   help without executing a callback, use `--mode help --target <name>`.
2. Read [CLI reference](references/cli-reference.md) for exact command families,
   current defaults, output files, prerequisites, and side effects.
3. For `m serve`, request/response fields, structured output, routing, streaming,
   multimodal messages, and error envelopes, read
   [Serving API](references/serving-api.md).
4. Before binding a socket or exposing a process, read
   [Deployment and configuration](references/deployment-and-config.md).
5. For missing extras, schema failures, port conflicts, backend errors, partial
   output, or command-safety recovery, read
   [Troubleshooting](references/troubleshooting.md).

## Safety gates

- Help and static inspection are safe. `m serve` imports user code and starts a
  blocking server; `m decompose` and `m eval` call models and write files;
  `m fix genslots` writes unless `--dry-run`; aLoRA commands may download a
  model, consume substantial compute, overwrite local files, prompt, or upload
  to Hugging Face Hub.
- Require an explicit decision before a public bind, provider call, model
  download, training run, remote upload, or non-dry-run rewrite. Never use a
  side-effectful command as an installation probe.
- Prefer `127.0.0.1` over the `m serve` wildcard default. The built-in service
  has no authentication, TLS, rate limiting, or authorization layer.
- Treat request `model` as untrusted routing metadata. Route only through a
  fixed allowlist; never derive a provider URL, import, credential, or arbitrary
  model loader directly from it.
- Validate `json_schema` before generation. A response schema affects output
  only when the served function accepts `format` and passes it into Mellea.
- True incremental streaming needs an uncomputed thunk and a streaming-capable
  backend. A computed result becomes one SSE content chunk.

## Minimal workflows

### Plan a serving request

1. Choose a local host and an unused port; prefer `127.0.0.1:8080`.
2. Confirm the app's `serve` signature and backend prerequisites without
   importing untrusted, side-effectful application code.
3. Draft one minimal request with `model` and a user message.
4. Add exactly one advanced feature at a time: `stream`, `response_format`,
   tools, multimodal content, or model routing.
5. Check `/health`, then send the bounded request and inspect the response or
   SSE `[DONE]` marker.

### Plan a CLI migration or pipeline

1. Render the exact nested help surface and check paths/credentials first.
2. For `fix`, run `--dry-run` and review every match before writing.
3. For `decompose` or `eval`, bound model/token/timeout settings and use a new
   output path; these commands make provider calls and files.
4. Inspect generated Python, validators, and result counts before executing or
   treating a run as successful.
5. Record which operations were deferred because they need a live backend,
   training resources, or remote write approval.

### Route a difficult request

- Structured-output endpoint with routing and streaming: read all of
  [Serving API](references/serving-api.md), use a fixed route allowlist, validate
  the JSON schema, and ensure the streaming branch returns an uncomputed thunk.
- Missing server extra: run help/static checks, install `server`, and repeat
  help; do not start Uvicorn as a dependency test.
- Decompose/fix misuse: read the failure table in
  [Troubleshooting](references/troubleshooting.md), preserve generated or
  rewritten artifacts, and recover with a narrower, reviewable operation.

## Ownership boundaries

Route provider selection, model identifiers, credentials, backend extras, and
provider failures to `../backends-and-models/SKILL.md`. Route evaluation design,
judge validity, and sampling semantics to
`../sampling-and-evaluation/SKILL.md`. Route tool execution, tool-call loops,
and MCP to `../tools-and-agents/SKILL.md` when that route is available; this
skill covers only the HTTP envelope and CLI boundary for tools.
