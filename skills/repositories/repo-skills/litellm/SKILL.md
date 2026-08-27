---
name: litellm
description: "Use for LiteLLM Python SDK, AI Gateway proxy, model routing,
  provider endpoint mapping, MCP/A2A agent tooling, pass-through routes,
  guardrails, virtual keys, spend tracking, and troubleshooting across
  OpenAI-compatible LLM providers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# LiteLLM

Use this skill when a task involves LiteLLM as a Python SDK or AI Gateway. LiteLLM provides OpenAI-format calls across many providers, a proxy server for centralized model access, routing and fallback policy, provider endpoint translation, and agent-tool integrations such as MCP and A2A.

## Start Here

1. If the user asks for direct Python calls, imports, streaming, embeddings, structured outputs, callbacks, caching, token/cost checks, or SDK errors, use [`sub-skills/sdk-core/SKILL.md`](sub-skills/sdk-core/SKILL.md).
2. If the user asks to run or configure the AI Gateway proxy, write YAML config, manage keys/teams/spend, configure guardrails, or check proxy health, use [`sub-skills/proxy-server/SKILL.md`](sub-skills/proxy-server/SKILL.md).
3. If the user asks about `Router`, model groups, fallbacks, retries, cooldowns, routing strategies, health-check routing, tags, aliases, or budget-aware routing, use [`sub-skills/routing/SKILL.md`](sub-skills/routing/SKILL.md).
4. If the user asks which provider prefix, endpoint helper, OpenAI-compatible route, pass-through target, or endpoint family to use, use [`sub-skills/providers-and-endpoints/SKILL.md`](sub-skills/providers-and-endpoints/SKILL.md).
5. If the user asks about MCP, A2A, Claude Code/Cursor agent gateway setup, tool approval, MCP auth/OAuth, or agent routes, use [`sub-skills/agent-tools/SKILL.md`](sub-skills/agent-tools/SKILL.md).

## Installation Patterns

- SDK-only usage: `pip install litellm` or `uv add litellm`.
- Proxy usage: `pip install 'litellm[proxy]'`, `uv tool install 'litellm[proxy]'`, or the project’s supported container/deployment path.
- Thin proxy client CLI usage: install the `cli` extra when a lightweight local client is enough.
- Optional workflows may require extras such as `caching`, `semantic-router`, `mlflow`, `google`, `proxy-runtime`, `extra_proxy`, `mcp`, or `a2a-sdk`; install only the extras required by the selected workflow.

## Minimal Checks

Run the bundled checker before debugging deeper issues:

```bash
python scripts/check_litellm_environment.py
python scripts/check_litellm_environment.py --check-proxy-cli
```

For live provider calls, confirm the provider key and model prefix first. Prefer mock/import/signature checks when the task is only code migration or configuration review.

## Shared References

- Read [`references/model-and-config-primer.md`](references/model-and-config-primer.md) for model naming, credential, parameter, and YAML conventions shared across SDK, proxy, router, and endpoint workflows.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install, import, credentials, network, optional dependency, and source-of-truth checks.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is current for a LiteLLM checkout or should be refreshed.

## Routing Boundaries

- SDK calls and endpoint selection overlap: use `sdk-core` for how to call LiteLLM and `providers-and-endpoints` for which endpoint/provider route is valid.
- Proxy config and routing overlap: use `proxy-server` for server/auth/admin operations and `routing` for model-group selection, fallback policy, and load-balancing semantics.
- Agent tools and proxy config overlap: use `agent-tools` for MCP/A2A protocol details and `proxy-server` for the underlying server, key, and deployment setup.
- Provider pass-through and agent routes overlap: use `providers-and-endpoints` for HTTP pass-through mechanics and `agent-tools` when the route exposes tools or agents to an IDE/agent client.

## Safe Verification Defaults

- Do not run live provider calls unless the user explicitly wants real API traffic and provides credentials.
- Do not start long-running proxy, database, benchmark, load, or deployment workflows unless the task requires them.
- Use bundled scripts for offline validation first: SDK smoke checks, proxy health checks, router config inspection, pass-through mock targets, and MCP tool-shape validation.
