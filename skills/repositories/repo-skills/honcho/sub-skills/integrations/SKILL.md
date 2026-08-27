---
name: integrations
description: "Use Honcho memory through Python and TypeScript SDKs, REST routes,
  MCP tools, webhooks, and agent-framework patterns."
metadata:
  disco-role: operating
disable-model-invocation: true
license: AGPL 3.0
---

# Honcho Integrations

Use this sub-skill when the task is to add, call, debug, or explain Honcho as a
memory layer in an application, agent, MCP client, webhook receiver, or
REST-only integration.

Honcho's integration loop is always the same:

1. Pick one stable **workspace** for the application or product surface.
2. Create stable **peers** for every durable participant: users, assistants,
   agents, bots, channels, or imported-data identities.
3. Put related turns or ingested records into coherent **sessions**.
4. Retrieve memory with fast reads (`context`, `representation`, `search`) or
   with the slower Dialectic `chat` endpoint when a reasoned answer is needed.
5. Record the user and assistant/tool output messages so background reasoning
   can update conclusions, representations, peer cards, summaries, and dreams.

## Route to references

| Need | Read or run |
| --- | --- |
| SDK object names, method names, REST route map, body fields, auth scope notes | `references/api-client-facts.md` |
| End-to-end Python, TypeScript, REST, multi-peer, conclusion, ingestion, and verification recipes | `references/workflows.md` |
| MCP tool use, coding-agent memory loop, framework integration hooks, feature flags, lazy imports | `references/mcp-agent-patterns.md` |
| Registering webhook endpoints, payload shape, signatures, delivery semantics | `references/webhooks.md` |
| Public example patterns to distill and source artifacts to exclude from runtime reuse | `references/source-candidates.md` |
| Common failures: no memory, empty context, 401/422, slow chat, webhook silence, MCP confusion | `references/troubleshooting.md` |
| Validate a proposed peer/session/message/read/webhook plan before coding | `scripts/validate_integration_plan.py` |
| Generate safe dry-run REST smoke commands for an integration | `scripts/rest_smoke_plan.py` |

## Decide the integration surface

- **Python SDK**: use `honcho-ai` when the target is Python code. The sync API is
  the default; async methods live under the `.aio` accessor on the same client,
  peer, session, and conclusion-scope objects.
- **TypeScript SDK**: use `@honcho-ai/sdk` when the target is Node, browser, or
  TypeScript agent code. Methods are promise-returning by default.
- **REST**: use `/v3/workspaces/{workspace_id}/...` routes when a codebase
  cannot take an SDK dependency or when debugging exact wire behavior.
- **MCP**: use the Honcho MCP server when an LLM client already supports MCP
  tools and the task is to give the agent persistent memory without editing an
  application codebase.
- **Webhooks**: use workspace webhooks when an app needs a push hint that queued
  representation or summary work drained for a session/observer pair. Treat
  webhook events as hints, then re-read state through the API.

Prefer a first-class environment integration when it exists. Otherwise embed the
SDK, or use raw MCP tools for agents that can call MCP but should not be edited.

## Minimal SDK shape

Python:

```python
from honcho import Honcho

honcho = Honcho(workspace_id="my-app", api_key=os.environ["HONCHO_API_KEY"])
user = honcho.peer("user-123")
assistant = honcho.peer("assistant")
session = honcho.session("chat-123")
session.add_messages([
    user.message("I prefer concise answers."),
    assistant.message("Got it — I will keep replies tight."),
])
context = session.context(summary=True, tokens=4000, peer_target=user.id)
answer = assistant.chat(
    "How should I adapt to this user?",
    target=user,
    session=session,
    reasoning_level="low",
)
```

TypeScript:

```typescript
import { Honcho } from "@honcho-ai/sdk";

const honcho = new Honcho({
  workspaceId: "my-app",
  apiKey: process.env.HONCHO_API_KEY,
});
const user = await honcho.peer("user-123");
const assistant = await honcho.peer("assistant");
const session = await honcho.session("chat-123");
await session.addMessages([
  user.message("I prefer concise answers."),
  assistant.message("Got it — I will keep replies tight."),
]);
const context = await session.context({
  summary: true,
  tokens: 4000,
  peerTarget: user,
});
const answer = await assistant.chat("How should I adapt to this user?", {
  target: user,
  session,
  reasoningLevel: "low",
});
```

## Integration decisions to record

Before implementing, write down these choices in the target codebase or plan:

- Workspace ID and where it is configured.
- Peer ID derivation for every participant. Use stable, safe IDs; do not mint a
  new user peer per request or per channel unless those really are separate
  people.
- Session granularity: per thread, channel, project, meeting, data source, or
  task. Keep related turns in one session while that context should cohere.
- Observation settings. `observe_me=false` is appropriate for deterministic
  bots; AI assistants may stay observed when their behavior is worth modeling.
  `observe_others` is per-session and controls theory-of-mind collection.
- Read strategy: near-instant `context`/`representation`/`search`, or slower
  `chat` for a reasoned answer. Pick the lowest `reasoning_level` that works.
- Record strategy: store user and assistant/tool messages after successful
  response generation, or store the user message before context retrieval only
  when the current turn should be included in the prompt window.
- Verification strategy: queue status or webhooks for readiness hints; direct
  representation/context/chat checks for memory quality.

## Rules and guardrails

- Use one workspace per application memory namespace. Multiple workspaces split
  a person's representation.
- Do not wait for background reasoning before responding. The next turn will
  see richer conclusions.
- Do not use Dialectic `chat` on every turn by default; it performs live
  reasoning and costs latency. Prefer `session.context()` for prompt grounding.
- Batch message creation accepts up to 100 messages. For larger imports, chunk
  batches and preserve `created_at` order.
- A conclusion query needs an observer/observed pair. SDK conclusion scopes add
  that automatically; raw REST callers must pass it in `filters`.
- For session context, requesting a peer perspective without a target is invalid.
  When no peer target is supplied, session context is recent messages and
  summaries only; it does not include cross-session memory.
- Webhook signatures are computed over the raw request body. Do not verify a
  re-serialized JSON body.
- MCP tools are workspace scoped. If the connection does not provide a workspace
  header, pass `workspace_id` explicitly on every workspace-scoped tool call.

## Before returning integration code

- Run or manually apply `scripts/validate_integration_plan.py` against the
  planned workspace, peers, sessions, messages, read paths, and webhook URLs.
- If using REST directly, generate a dry-run smoke sequence with
  `scripts/rest_smoke_plan.py` and adapt the printed commands to the target
  environment.
- Check `references/troubleshooting.md` for any symptom that matches failing
  setup, auth, context, chat, conclusion, webhook, or MCP behavior.
