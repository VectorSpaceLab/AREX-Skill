---
name: platform-pipeline-provider
description: "Develop and debug LangBot platform adapters, HTTP Bot callbacks,
  message aggregation, pipeline stages, provider runners, model managers, local
  agent tools, and tool-loading workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Platform, Pipeline, and Provider

Use this sub-skill for message flow, IM platform adapters, HTTP Bot and WebSocket
chat behavior, pipeline stages, providers/runners, model manager, local agent,
and tool manager issues.

## Read First

- [references/message-flow-and-pipelines.md](references/message-flow-and-pipelines.md)
  for the inbound-to-outbound runtime graph and stage ownership.
- [references/platform-adapters.md](references/platform-adapters.md) for adapter
  manifests, webhook routing, adapter boundaries, and platform pitfalls.
- [references/providers-and-tools.md](references/providers-and-tools.md) for
  model providers, runners, local agent, tool loaders, and plugin/MCP/native
  tool boundaries.
- [references/http-bot-workflow.md](references/http-bot-workflow.md) for the
  signed HTTP Bot server-to-server adapter.
- [references/troubleshooting.md](references/troubleshooting.md) for callback,
  signature, aggregation, provider, and tool failures.

## Common Workflows

### Trace one message

1. Platform adapter converts native event into shared message/event entities.
2. `RuntimeBot` applies routing rules and pushes messages to aggregation.
3. `MessageAggregator` collapses N-to-1 bursts by session.
4. `Controller` schedules `Query` work subject to concurrency.
5. `RuntimePipeline` executes configured stages.
6. Chat stage invokes providers/tools/plugins and records session/history.
7. Output stages send responses through the adapter.

### Add or change an adapter

Keep vendor translation inside the adapter. Do not put LLM provider logic or
pipeline business rules inside platform code. Add or update manifests, config
schemas, icons/assets, i18n strings, docs, and focused adapter tests.

### Debug provider/tool behavior

Start with fake provider/tool tests before using real API keys. If plugin,
Box, native, or stdio MCP tools are involved, route deep runtime details to
`plugin-box-skills` after confirming the provider/tool manager boundary.

## Bundled Helper

Use [scripts/http_bot_hmac_helper.py](scripts/http_bot_hmac_helper.py) for
self-contained HTTP Bot HMAC signing, verification, payload building, and
optional signed POSTs. It adapts the public example client into a skill-owned
helper and does not depend on the original checkout.

## Focused Checks

```bash
python scripts/select_langbot_checks.py pipeline
uv run pytest tests/smoke/test_fake_message_flow.py -q --tb=short
uv run pytest tests/integration/pipeline/test_full_flow.py -q --tb=short
uv run pytest tests/unit_tests/platform/test_http_bot_tenancy.py -q --tb=short
uv run pytest tests/unit_tests/provider/test_tool_manager.py -q --tb=short
```
