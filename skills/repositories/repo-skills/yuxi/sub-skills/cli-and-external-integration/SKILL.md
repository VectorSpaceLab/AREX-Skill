---
name: cli-and-external-integration
description: "Operate and extend yuxi-cli plus the external API/SSE integration
  flows it drives."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# cli-and-external-integration

This sub-skill owns the public CLI surface and the external HTTP/SSE flows that
the CLI exercises.

## Load this sub-skill when

- The task touches `yuxi`, `python -m yuxi_cli`, or the CLI package help/config
  surface.
- You need remote discovery, login, whoami, status, logout, or the local
  browser chat helper.
- You need `kb upload`, `kb list/files/query/open/find`, or `agent eval`.
- You need to debug API-key auth, SSE parsing, or Langfuse dataset experiment
  wiring.

## Do not use this sub-skill when

- The task is backend runtime behavior, deployment bootstrap, OCR/parser
  internals, or knowledge-base storage/indexing internals.
- You are about to write or delete remote data without explicit approval and the
  required credentials/services.

## Owned surface

- CLI install/config/remotes/login/status/logout/chat/agent/kb commands.
- Browser chat helper and its local NDJSON bridge.
- External API auth, discovery, SSE streaming, and Langfuse experiment calls.
- Safe offline smoke checks before any live integration work.

## Safe operating rules

- Run `scripts/check-cli.sh` first. It is offline by default.
- Treat `kb upload` and `agent eval` as side-effectful.
- Use a live remote only after discovery/version/capability checks succeed.
- Keep API keys, dataset secrets, and Langfuse credentials out of logs and
  examples.
- Use HTTPS for non-local remotes.

## First-line entry points

- Offline smoke: `scripts/check-cli.sh`
- CLI entry: `yuxi` or `python -m yuxi_cli`
- Command map and proof points: `references/cli-command-map.md`
- External API and eval examples: `references/external-api-and-eval.md`
- Failure triage: `references/troubleshooting.md`

## Change order

1. Decide whether the task is offline CLI work or a live remote flow.
2. If offline, adjust command wiring, client wrappers, or help text and keep the
   smoke script green.
3. If live, verify discovery, auth, and capability gates before calling the
   remote.
4. Match each behavior change with the CLI tests named in the command map.
