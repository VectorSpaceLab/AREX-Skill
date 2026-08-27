---
name: local-serving
description: "Guides OpenLLM local model serving, terminal chat,
  OpenAI-compatible localhost APIs, and readiness troubleshooting for `openllm
  hello`, `openllm serve`, and `openllm run`."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Local Serving

Use this sub-skill when the task is about starting or diagnosing a local OpenLLM model server.

## Typical triggers

- `openllm serve MODEL[:VERSION]`
- `openllm run MODEL[:VERSION]`
- `openllm hello`
- Chat UI at `/chat`
- OpenAI-compatible localhost `/v1` API
- Server readiness, port selection, or environment-variable forwarding
- Gated model access via `HF_TOKEN`

## What this route covers

- `openllm serve` and `openllm run` command semantics.
- Default port behavior and the difference between browser chat and terminal chat.
- `--env` and `--arg` forwarding.
- `ensure_bento`-driven model selection and the meaning of missing or ambiguous model tags.
- Readiness checks and common startup failures.

## Read next

- [references/cli-reference.md](references/cli-reference.md) for command options and defaults.
- [references/workflows.md](references/workflows.md) for runbooks and examples.
- [references/troubleshooting.md](references/troubleshooting.md) for startup, readiness, and model-loading failures.
- [scripts/build_serve_command.py](scripts/build_serve_command.py) when you want a safe command planner instead of starting a server.
- [scripts/check_local_server.py](scripts/check_local_server.py) when you want to probe a running local server.

## Boundaries

Do not route model repository management to this sub-skill. If the issue is a stale model cache, missing repository alias, or custom repo URL, switch to `model-repositories`. If the issue is BentoCloud deployment or cleanup, switch to the owning sub-skill.
