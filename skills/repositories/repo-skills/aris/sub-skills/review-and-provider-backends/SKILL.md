---
name: review-and-provider-backends
description: "Configure and troubleshoot ARIS cross-model reviewers, MCP
  bridges, OpenAI-compatible providers, MiniMax, Claude/Gemini overlays, manual
  review, and optional Feishu/Lark integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Review and Provider Backends

Use this sub-skill when ARIS needs an external reviewer, MCP server registration, an alternative LLM endpoint, a manual human review handoff, a Claude/Gemini/Codex combination, MiniMax or ModelScope configuration, Feishu/Lark notification, or a Codex image bridge.

## Route Here

- Configure the default Claude executor + Codex MCP reviewer path.
- Configure Codex executor + Claude/Gemini reviewer overlays.
- Use a generic OpenAI-compatible `llm-chat` backend or MiniMax instead of Codex MCP.
- Run manual review in browser or headless file mode.
- Diagnose provider credentials, model names, retries, timeouts, MCP registration, protocol negotiation, and restart requirements.
- Preserve cross-model independence and provenance evidence.

## Reroute

- Host skill directory, manifest, or selective install: `../install-and-distribution/SKILL.md`.
- Workflow selection and assurance levels: `../workflow-routing-and-skill-catalog/SKILL.md`.
- Research state, trace files, or watchdog: `../state-recovery-and-experiment-ops/SKILL.md`.
- Source edits or mocked server tests: `../repository-maintenance/SKILL.md`.

## Safe Backend Pattern

1. Identify executor family and reviewer family.
2. Pick one reviewer route and record its model, server name, endpoint, and credential source.
3. Register MCP before invoking a workflow, then restart the host agent.
4. Validate with a trivial tool call before spending a full review request.
5. Keep raw review artifacts and traces; never let the executor summarize away a failure.
6. If a provider is unavailable, switch to an explicitly configured alternative or mark the review blocked.

## Reference Map

- `references/provider-matrix.md` compares reviewer/provider routes, required environment variables, and independence implications.
- `references/mcp-servers.md` summarizes the optional server contracts and testable failure modes.
- `references/troubleshooting.md` covers keys, endpoints, protocol, model, timeout, and local handoff failures.
- Root `../../references/repo-provenance.md` and `../../references/troubleshooting.md` provide provenance and cross-cutting diagnosis.

## Avoid

- Never publish API keys, bearer tokens, raw provider error bodies, or local debug paths in artifacts.
- Do not call a same-family reviewer and label it independent.
- Do not treat mocked MCP unit tests as proof of live provider connectivity.
- Do not install every provider dependency when one selected reviewer path is enough.
