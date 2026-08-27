# Source Examples and Adaptation Candidates

## Purpose

Use this as a distilled map of public examples and integration snippets that are
useful to adapt for Honcho integrations. The original examples are evidence, not
runtime dependencies.

## High-value patterns to distill

| Source example family | What to distill | Bundle or owner |
| --- | --- | --- |
| Python SDK quickstart and SDK docs | Client init, peer/session creation, `add_messages`, `context`, `chat`, `representation`, async `.aio` usage | `references/api-client-facts.md` and `references/workflows.md` |
| TypeScript SDK quickstart and SDK docs | Promise-based client init, `addPeers`, `addMessages`, `context`, `chat`, `representation`, `conclusions` scopes | `references/api-client-facts.md` and `references/workflows.md` |
| LangGraph examples | State-graph turn handling, prefetch before model call, record after response | `references/workflows.md` |
| CrewAI example | Honcho-backed memory storage and explicit retrieval tools | `references/workflows.md` |
| Gmail importer example | External identity normalization, thread-to-session mapping, timestamp metadata, quoted-reply stripping | `references/workflows.md` |
| Granola importer example | Meeting-to-session mapping, participant modeling, transcript preprocessing | `references/workflows.md` |
| Zo Computer integration skill | Save/query/context loop and one-workspace-one-session memory strategy | `references/workflows.md` |
| n8n workflow example | Low-code ingestion plus chat stage separation | `references/workflows.md` |
| MCP instructions and README | Tool families, workspace header behavior, chat/context/sync sequence | `references/mcp-agent-patterns.md` |
| Webhook docs | Event structure, signature verification, no-retry delivery model | `references/webhooks.md` |

## Exclude from runtime reuse

| Source artifact type | Why it should not be copied verbatim |
| --- | --- |
| OAuth-heavy importer scripts | They depend on live third-party consent, local secret files, and external APIs. Distill the mapping logic, not the credential flow. |
| Long framework demo apps | They are useful as examples, but future agents need concise workflow guidance and smaller snippets. |
| Dashboard or marketplace instructions | They are environment-specific and may change independently of the SDK/API surface. |
| Direct source-repo path links | The generated skill must stand alone after the original checkout is gone. |

## Bundling guidance

- Copy only the reusable memory integration pattern.
- Preserve any safe helper logic that normalizes IDs, splits sessions, or
  handles message batching.
- Replace network-heavy or credential-heavy behaviors with a dry-run reference
  or a tiny validation script when practical.
