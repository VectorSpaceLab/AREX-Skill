---
name: quality-safety-governance
description: "Owns safety policies, anonymization, reflection, reliability,
  eval, tracing, prompt logging, and usage-governance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# quality-safety-governance

Use this route for safety policies, anonymization, reflection, reliability, evals, tracing, prompt logging, and usage-governance questions.

## Include

- `safety_engine` policies and anonymization utilities.
- `reflection` configuration and processing.
- `reliability_layer` and evaluation-related control flow.
- Tracing and observability integrations such as `TracingProvider`, `DefaultTracingProvider`, and `PromptLayer`.

## Exclude

- Tool schema and MCP mechanics → [tools-and-mcp](../tools-and-mcp/SKILL.md)
- Core runtime execution → [agent-runtime](../agent-runtime/SKILL.md)
- Persistent chat/session storage → [chat-memory-storage](../chat-memory-storage/SKILL.md)

## Start here

- [references/safety-policies.md](references/safety-policies.md)
- [references/reliability-evaluation.md](references/reliability-evaluation.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/check_policy_imports.py](scripts/check_policy_imports.py)
