---
name: llm-providers
description: "Routes provider aliases and async LLM calls for giskard-llm."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LLM Providers

Use this sub-skill for direct `giskard.llm` routing, provider configuration,
and async provider calls.

## Read First

- [API reference](references/api-reference.md) for verified client, helper,
  type, and error surfaces.
- [Provider matrix](references/provider-matrix.md) for prefixes, extras,
  credentials, operations, and provider-specific caveats.
- [Workflows](references/workflows.md) for alias configuration and async
  completion, embedding, and response calls.
- [Troubleshooting](references/troubleshooting.md) for missing SDKs,
  authentication, unsupported operations, bad requests, and retry decisions.
- [scripts/inspect_llm_routing.py](scripts/inspect_llm_routing.py) for no-key
  installed-package routing inspection without live provider calls.

## Use This When

- The user is choosing or configuring a provider alias.
- The user has a `provider/model` string or a bare model name.
- The user needs async completions, embeddings, or stateful responses.
- The user needs to know which SDK extra or auth env var is required.
- The user needs retry guidance for provider errors.

## In Scope

- `LLMClient`, `configure`, `reset`, `acompletion`, `aembedding`, `aresponse`,
  and `should_retry`
- Provider prefixes and alias routing, including bare-model defaulting
- Public message, tool, choice, response, and error types
- Provider extras, auth env vars, and transport kwargs
- Error mapping and retry decisions

## Route Elsewhere

- Chat workflows, tools, templates, and workflow orchestration -> `../agents-workflows/SKILL.md`
- Judges, scenarios, suites, and eval checks -> `../checks-evals/SKILL.md`

## Quick Rule

Start with the provider matrix. Use the inspector script when you need to
confirm installed SDK availability or parse model strings without calling a live
provider.
