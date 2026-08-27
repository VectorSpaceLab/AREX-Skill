---
name: agents-workflows
description: "Use for giskard.agents async chat workflows, tools, prompt
  templates, structured outputs, retries, rate limiting, embeddings, and
  optional LiteLLM backend."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# agents-workflows

Use this sub-skill when the task is to build or debug async `giskard.agents`
chat workflows, generator orchestration, tools, prompt templates, structured
outputs, retries/rate limiting, embedding wrappers, or the optional LiteLLM
backend.

## Route first

- For provider aliases, SDK installation, credentials, API-key environment
  variables, and direct `giskard.llm` completion/embedding calls, route to
  [llm-providers](../llm-providers/SKILL.md).
- For `Scenario`, `Suite`, deterministic checks, LLM judges, eval reports, and
  JUnit export, route to [checks-evals](../checks-evals/SKILL.md).
- Keep provider calls inside `BaseGenerator` subclasses. Workflows, tools, and
  prompt templates should stay provider-agnostic and operate on Giskard message,
  tool, and response objects.

## Read these references

- [API reference](references/api-reference.md) for verified public classes,
  constructors, methods, and ownership boundaries.
- [Workflows](references/workflows.md) for async chat, multi-message prompts,
  templates, tools, structured output, middleware, LiteLLM, and embeddings.
- [Troubleshooting](references/troubleshooting.md) for missing LiteLLM, provider
  setup boundaries, tool schema/coercion, template namespaces, workflow errors,
  structured-output retries, and rate limiter behavior.

## Safe local check

Run the bundled no-provider smoke script when validating that an installed
package exposes the core agents/tool workflow surface:

```bash
python sub-skills/agents-workflows/scripts/run_agents_smoke.py
```

The script uses a deterministic local `BaseGenerator` and `@tool`; it does not
make provider, network, credential, or repository-checkout calls.
