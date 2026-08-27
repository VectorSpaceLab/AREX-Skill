---
name: mcp-tools
description: "Operate DeepKE's local MCP service wrapper for NER, RE, AE, and EE
  extraction tools without relying on source checkout documentation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepKE MCP Tools

Use this sub-skill when the task is to expose DeepKE extraction through an MCP-compatible local server, configure a Cursor/Cline-like MCP client entry, understand the `deepke_ner`, `deepke_re`, `deepke_ae`, or `deepke_ee` tool arguments, or diagnose environment problems around `DEEPKE_PATH`, `CONDA_PY`, `CONDA_EE_PY`, API-client variables, and `mcp.server.fastmcp` imports.

Do **not** use this sub-skill as proof that an extraction model is available. The MCP wrapper only shells out to local DeepKE example predictors; trained checkpoints, compatible example configs, and a trusted local checkout are still required for real predictions.

## Quick route

1. For deployment and client/server wiring, read [references/workflows.md](references/workflows.md).
2. For exact tool signatures, task-mode limits, return text, and side effects, read [references/tool-api-reference.md](references/tool-api-reference.md).
3. For failures around missing variables, `mcp` versions, absent checkpoints, source config mutation, client API errors, or path handling, read [references/troubleshooting.md](references/troubleshooting.md).
4. Before launching a server, run [scripts/check_mcp_env.py](scripts/check_mcp_env.py) to verify imports and environment-variable presence without starting the service or calling models.
5. When only the event-extraction TSV/raw input conversion is needed, run [scripts/convert_text_to_tsv.py](scripts/convert_text_to_tsv.py); it is a standalone adaptation of the pure conversion helper and does not import DeepKE.

## Operating guardrails

- Treat the local MCP server as a wrapper around mutable local DeepKE example directories, not as a stateless API.
- The original server edits prediction/training YAML files and event-extraction data files before shelling out. Only run it when the downstream task explicitly asks to operate a local DeepKE checkout and the user accepts those mutation risks.
- Keep all path and credential values in environment variables or client settings; do not write private paths, API keys, or local environment names into generated artifacts.
- Prefer the bundled diagnostic and conversion scripts for safe checks. They do not launch the MCP server, invoke LLM APIs, run DeepKE predictors, or mutate DeepKE configs.
