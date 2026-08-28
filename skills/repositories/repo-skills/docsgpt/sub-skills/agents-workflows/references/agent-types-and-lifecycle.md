# Agent Types and Lifecycle

## Shared components

An agent combines:

- name/description and publish state;
- system prompt or prompt reference;
- source ids and retrieval settings;
- selected provider/model;
- tools plus per-action approvals;
- type-specific limits;
- API key, webhook token, sharing/team scope and logs.

Agent API keys resolve the bound prompt, sources, tools and default model. Request-level fields do not necessarily override key-owned configuration.

## Type behavior

### Classic

Retrieves configured source context up front, composes it into the prompt, then generates and may call tools. Use when evidence should predictably accompany each answer.

### Agentic

Exposes `internal_search` so the model can decide whether to search, issue several refined queries, or skip retrieval. Use when tasks vary and browse-as-you-go is useful. Bound tool loops and inspect search traces.

### Research

Runs clarification, planning, iterative research and synthesis. Configure request, token, step and timeout budgets. Use for multi-source investigations; do not use it for a single deterministic lookup.

### Workflow

Executes an explicit graph of start/end, agent, state, condition, note and code nodes. Use when branches, shared state, repeatable steps or artifact/file handoff matter.

## Design checklist

- Define an answer contract: prose, citation requirements, or JSON Schema.
- Choose a model whose catalog capabilities match tools, structured output, streaming and attachments.
- Use prompts to state what to do when evidence is missing; do not force fabricated answers.
- Set source exposure: prefetch for predictable context, agentic tool for on-demand search.
- Minimize tools and credentials; enable approval for side effects.
- Test prompt-template variables and passthrough values explicitly.
- Use stable model ids and source ids.
- Review token usage and logs per agent.

## Lifecycle

1. create as draft;
2. configure prompt/model/sources/tools;
3. test privately;
4. publish or share with explicit role;
5. rotate API/webhook keys when exposed;
6. monitor logs, feedback and token usage;
7. version/export where supported;
8. revoke/unpublish before destructive removal.

## Structured output

Agent/workflow nodes can carry a JSON Schema. Validate required fields and failure behavior with the selected model/provider. Schema support in a model catalog is a capability claim, not proof that every schema will be followed; use strict validation and recovery.

## Headless versus interactive

Schedules/webhooks do not have an active browser. Remove tools that need approval UI, device presence, OAuth completion, conversational clarification, or recursive scheduling unless the headless runner has a defined alternative.
