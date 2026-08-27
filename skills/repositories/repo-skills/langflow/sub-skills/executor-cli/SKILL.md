---
name: executor-cli
description: "Use and maintain lfx, lfx run, lfx serve, lfx-mcp, Flow DevOps
  commands, and stateless executor semantics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Executor CLI

Use this sub-skill when the task involves the lightweight Langflow Executor (`lfx`), Flow DevOps CLI workflows, local flow execution, serving flow JSON as a small API, `lfx-mcp`, or debugging stateless executor behavior.

## Read First

- [CLI reference](references/cli-reference.md): command map, `lfx run`, `lfx serve`, Flow DevOps commands, extension commands, `lfx-mcp`, and safe command templates.
- [Stateless runtime](references/stateless-runtime.md): what persists, what does not, credential/request-variable behavior, `NoopSession`, `--flow-dir`, and memory/session caveats.
- [Troubleshooting](references/troubleshooting.md): install/import, optional dependency, flow schema, variable, API-key, network, and runtime failure signals.
- [Flow validation helper](scripts/validate_lfx_flow.py): offline JSON parse/shape check that prints safe `lfx validate`, `lfx run`, and `lfx serve` command templates without executing the flow.

## Use This For

- Running a local flow JSON or Python graph with `lfx run`, including path, `--stdin`, and `--flow-json` modes.
- Serving one or more flow JSON files with `lfx serve`, including API-key setup, `.env` files, `--flow-dir`, multi-worker behavior, uploads, streaming, and `--no-env-fallback`.
- Flow DevOps tasks with `lfx init`, `create`, `validate`, `requirements`, `upgrade`, `status`, `push`, `pull`, and `export`.
- MCP server startup and remote Langflow flow-building control through `lfx-mcp`.
- Explaining why LFX does not provide full Langflow database/server persistence.

## Route Elsewhere

- Full Langflow server, database, auth, migrations, and service internals belong in `../backend-runtime/SKILL.md`.
- SDK client code, REST client implementation, and Python API integrations belong in `../sdk-and-api-clients/SKILL.md`.
- Component class authoring, bundles, and component-index maintenance belong in `../component-development/SKILL.md`.
- Production container/deployment operations beyond `lfx serve` belong in `../deployment-and-operations/SKILL.md`.

## Fast Workflow

1. Identify whether the user needs one-shot execution (`lfx run`), an HTTP endpoint (`lfx serve`), Flow DevOps sync (`status`/`push`/`pull`/`export`), extension inspection (`lfx extension ...`), or MCP (`lfx-mcp`).
2. Validate the flow file offline before suggesting execution:
   ```bash
   python scripts/validate_lfx_flow.py path/to/flow.json
   ```
3. If the flow contains provider components, confirm required component packages and credentials are installed/configured before running or serving.
4. For `lfx serve`, require a local `LANGFLOW_API_KEY` or `LFX_API_KEY` token and decide whether process-env fallback is acceptable; use `--no-env-fallback` for request-scoped credentials.
5. For multi-worker serving, use `--flow-dir` with JSON flows only; do not use `.py` script flows with `--workers > 1 --flow-dir`.

## Safety Notes

- Do not execute untrusted flow JSON or Python graph scripts just to inspect them; use the bundled helper and `lfx validate` first.
- Do not paste real API keys into examples, flow JSON, or committed `.lfx/environments.yaml`; store key values in environment variables.
- Treat `lfx run` and `lfx serve` as stateless executor paths, not replacements for the full Langflow app database.
