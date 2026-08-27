---
name: studio-runtime
description: "Launch, secure, connect, operate, and troubleshoot Unsloth Studio
  servers, backend APIs, tool policy, providers, RAG, GGUF inference, and
  runtime setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Studio Runtime

Use this sub-skill when the task is about Unsloth Studio as a local web/API runtime: installing or updating Studio, launching the server, exposing it safely, connecting coding agents, managing backend API routes, configuring inference providers, running GGUF or llama.cpp-backed chat, using RAG/data recipes, handling tool execution policy, inspecting hardware, or debugging Studio startup/runtime failures.

Do not use this sub-skill for code-first Unsloth training APIs; route those tasks to [core-training](../core-training/SKILL.md). For full CLI syntax catalogs and non-Studio CLI workflows, route to [cli-workflows](../cli-workflows/SKILL.md). For deep export/merge/GGUF conversion details, route to [model-export](../model-export/SKILL.md).

## Quick Routing

- For install, update, uninstall, launch, secure tunnel, one-line model serving, coding-agent connection, and environment/storage planning, read [references/studio-workflows.md](references/studio-workflows.md).
- For backend API route groups, auth/API keys, OpenAI-compatible endpoints, provider/model/RAG/data recipe endpoints, and system probes, read [references/api-and-routes.md](references/api-and-routes.md).
- For host binding, Cloudflare tunnel safety, API key exposure, server-side tools, MCP stdio policy, provider credentials, RAG file access, and remote-code risk, read [references/security-and-tools.md](references/security-and-tools.md).
- For startup, setup, `UNSLOTH_STUDIO_HOME`, frontend assets, llama.cpp/GGUF/mmproj/cache/context, provider, RAG, GPU/MLX/ROCm, shutdown, and connection failures, read [references/troubleshooting.md](references/troubleshooting.md).
- Before changing a user's machine, run the safe local checker [scripts/studio_preflight.py](scripts/studio_preflight.py) to inspect flags, environment variables, expected Studio paths, and CLI help without starting a server, installing packages, or opening network connections.

## Operating Principles

- Prefer `unsloth studio --secure` for remote browser/API access: it keeps the raw server on loopback and fails closed if the Cloudflare HTTPS tunnel cannot start.
- Treat `unsloth studio -H 0.0.0.0` as an explicit raw network bind; warn that anyone with the server URL and API key can access the server and, if tools are enabled, run server-side tools as the local user.
- Keep `UNSLOTH_STUDIO_HOME` consistent across setup and launch when using an isolated Studio root; mismatched roots can look like missing setup, missing frontend assets, stale auth, or missing llama.cpp.
- Use `unsloth studio run --model ...` for one-command serving plus API-key creation; use plain `unsloth studio` when the user wants the UI/runtime without auto-loading a model.
- Use `unsloth connect` for coding-agent integration; remote Studio servers need an explicit saved API key, while verified local loopback servers can mint and cache a key automatically.
- Keep runtime troubleshooting non-destructive first: inspect help, env vars, paths, ports, route health, model status, provider credentials, RAG availability, and llama.cpp freshness before advising setup/update/uninstall scripts.
