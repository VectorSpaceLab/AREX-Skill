---
name: mcp-server
description: "Guide strands-agents-mcp-server installation, CLI use, docs
  search/fetch semantics, llms.txt indexing, cache hydration, URL restrictions,
  environment variables, and offline/live tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MCP server

Use this sub-skill when working on the `strands-agents-mcp-server` package and
its documentation-access tools.

## Start here

1. Read [overview.md](references/overview.md) for package boundaries, verified facts, and owned behavior.
2. Read [cli-reference.md](references/cli-reference.md) for install, launch, environment variables, and safe check commands.
3. Read [workflows.md](references/workflows.md) for `search_docs`, `fetch_doc`, hydration, sectioning, and test workflows.
4. Read [troubleshooting.md](references/troubleshooting.md) for expected error dictionaries, network issues, prefetch timing, and dependency warnings.
5. Use [mcp-smoke.sh](scripts/mcp-smoke.sh) for import/signature and console-help checks without network fetches.
6. Use [mcp-unit-check.sh](scripts/mcp-unit-check.sh) for selected offline unit tests when invoked from a compatible checkout.

## Use this sub-skill for

- Installing or launching the docs-search MCP server through the console entry point, module entry point, or MCP client command.
- `search_docs(query, k=5)` ranking, snippets, result fields, and hydration-sensitive body-term search.
- `fetch_doc(uri="", section="")` catalog mode, TOC mode, section mode, small-document behavior, and error shapes.
- `llms.txt` catalog indexing, cache hydration, snippet generation, background prefetch, retryable indexing failures, and section extraction.
- URL restrictions, server environment variables, dependency warnings, offline unit tests, and live-doc integration tests.

## Route elsewhere

- Python SDK MCP client internals, transport adapters, or `MCPClient` usage by agents: use [python-sdk](../python-sdk/SKILL.md).
- Docs-site MDX pages, `sourceLinks`, generated API docs, or site navigation: use [docs-site](../docs-site/SKILL.md).
- TypeScript SDK MCP client/tools: use [typescript-sdk](../typescript-sdk/SKILL.md).

## Operating rules

- Do not fetch live documentation, run networked integration tests, or start long-lived inspectors by default.
- Preserve the strict allowed host: only HTTPS URLs under `strandsagents.com` are valid document URLs.
- Treat search scores as within-query ordering values, not probabilities or cross-query comparable numbers.
- Keep unsupported URL, fetch failure, and unknown section errors as explicit dictionary returns unless the package contract changes deliberately.
- Keep live-doc network tests separate from offline unit tests; skip or document them unless the task explicitly selects network verification.

## Fast path

1. Identify whether the task is packaging/launch, search ranking, fetch/sectioning, cache/indexing, URL validation, or tests.
2. Read the matching reference and run the smoke helper in an environment where the package is installed.
3. For behavior changes, prefer offline unit tests first; escalate to live docs only when the task requires real public site behavior.
4. If a task crosses into SDK MCP client behavior, hand off to the Python or TypeScript SDK sub-skill instead of mixing contracts.
