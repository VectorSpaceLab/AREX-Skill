# MCP and Agent Integration Patterns

## Purpose

Read this when the task is to give an MCP-capable assistant Honcho memory, wire
Honcho into an agent framework conceptually, or design code hooks for a bot,
workflow engine, or coding agent.

## Raw MCP quick flow

The hosted Honcho MCP server exposes workspace, peer, session, conclusion, and
system tools. Connect with an Honcho API key and, when possible, provide an
`X-Honcho-Workspace-ID` header so every workspace-scoped tool can omit
`workspace_id`. If no workspace header is configured, pass `workspace_id` on
every workspace-scoped tool call.

Typical turn loop:

1. Once per conversation, create or get a session.
2. Create stable peers for the user and assistant.
3. Add the peers to the session with observation settings.
4. Before responding, use fast reads (`get_session_context`, `get_peer_context`,
   `get_representation`, or `search`) when they are enough; use `chat` when a
   reasoned answer is worth a few seconds of latency.
5. After responding, call `add_messages_to_session` with both the exact user
   message and the exact assistant response.

Minimal tool-call sequence:

```text
create_session
  workspace_id: "my-app"
  session_id: "chat-123"

create_peer
  workspace_id: "my-app"
  peer_id: "user-123"

create_peer
  workspace_id: "my-app"
  peer_id: "Assistant"

add_peers_to_session
  workspace_id: "my-app"
  session_id: "chat-123"
  peers:
    - peer_id: "user-123"
      observe_me: true
      observe_others: true
    - peer_id: "Assistant"
      observe_me: false
      observe_others: true

chat
  workspace_id: "my-app"
  peer_id: "Assistant"
  target_peer_id: "user-123"
  session_id: "chat-123"
  query: "What communication style does this user prefer?"

add_messages_to_session
  workspace_id: "my-app"
  session_id: "chat-123"
  messages:
    - peer_id: "user-123"
      content: "<exact user message>"
    - peer_id: "Assistant"
      content: "<exact assistant response>"
```

## MCP tool families

| Family | Tools | When to use |
| --- | --- | --- |
| Workspace | `list_workspaces`, `create_workspace`, `inspect_workspace`, `search`, `get_metadata`, `set_metadata` | Discover or create the memory namespace; search messages across optional peer/session scopes. |
| Peers | `create_peer`, `list_peers`, `chat`, `get_peer_card`, `set_peer_card`, `get_peer_context`, `get_representation` | Create participants and retrieve peer memory. |
| Sessions | `create_session`, `list_sessions`, `delete_session`, `clone_session`, `add_peers_to_session`, `remove_peers_from_session`, `get_session_peers`, `inspect_session`, `add_messages_to_session`, `get_session_messages`, `get_session_message`, `get_session_context` | Manage conversation buckets and record/retrieve turns. |
| Conclusions | `list_conclusions`, `query_conclusions`, `create_conclusions`, `delete_conclusion` | Inspect, add, or remove derived or manually curated facts. |
| System | `schedule_dream`, `get_queue_status` | Consolidate memory or check background processing. |

## Good MCP memory queries

Use `chat` sparingly for questions that require synthesis:

- "What does this user value most in technical explanations?"
- "What unstated constraints should I remember for this project?"
- "How should I adapt tone for this user?"
- "What changed between this user's earlier and current goals?"

Prefer fast reads for prompt grounding:

- `get_session_context` for current session history and optional peer
  representation.
- `get_representation` for a concise memory block about a peer.
- `get_peer_context` for representation plus peer card.
- `search` for specific past message retrieval.

## Agent-framework integration hooks

When embedding Honcho into an agent framework rather than using raw MCP, place
Honcho at these hook points.

### Configuration

Add a configuration section:

```text
honcho.enabled: boolean
honcho.workspace_id: string
honcho.context_tokens: integer or null
honcho.prefetch: boolean
honcho.base_url: optional string
honcho.assistant_peer_id: string
```

Gate every runtime call on both `enabled` and presence of credentials. A bot or
agent framework should start normally when Honcho is disabled or credentials are
unset.

### Client factory

Create one lazy client factory per process. It should:

- Read workspace ID, API key, and base URL from environment/config.
- Avoid top-level hard imports in optional integrations when the SDK dependency
  is optional.
- Return the same client instance when repeated calls use the same configuration.
- Log actionable warnings without exposing API keys.

Python optional dependency pattern:

```python
def get_honcho_client(config):
    if not config.enabled:
        return None
    try:
        from honcho import Honcho
    except ImportError:
        logger.warning("Honcho is enabled but honcho-ai is not installed")
        return None
    if not os.getenv("HONCHO_API_KEY"):
        logger.warning("Honcho is enabled but HONCHO_API_KEY is unset")
        return None
    return Honcho(workspace_id=config.workspace_id, base_url=config.base_url)
```

TypeScript optional dependency pattern:

```typescript
async function getHonchoClient(config) {
  if (!config.enabled) return null;
  if (!process.env.HONCHO_API_KEY) return null;
  const { Honcho } = await import("@honcho-ai/sdk");
  return new Honcho({ workspaceId: config.workspaceId, baseURL: config.baseURL });
}
```

### ID mapping

Map framework identities to stable Honcho IDs:

- User peer: a durable account ID when possible; otherwise a normalized channel
  user ID.
- Assistant peer: one shared assistant ID per agent persona.
- Tool peers: only create separate peers for tools/subagents if their behavior
  or perspective should be modeled.
- Session ID: stable per thread, project, channel, run, or task. Do not mint a
  new session per single message unless the messages are unrelated.

Use a safe normalizer for external IDs. A conservative rule is letters, digits,
underscore, and hyphen only, with other characters collapsed to hyphens.

### Prefetch hook

Run before the model call when low-latency prompt grounding is wanted:

1. Ensure peers and session exist.
2. Store the current user message first only if current-turn inclusion is
   desired.
3. Fetch `session.context(tokens=..., peer_target=user, peer_perspective=assistant)`.
4. Convert to the model provider's chat format.
5. Inject the result into the system prompt or message list.

### Tool hook

Register a tool such as `query_user_memory`. The handler calls
`assistant.chat(query, target=user, session=session, reasoning_level="low")`.
Expose optional reasoning level only to trusted agent logic; do not let end users
force `max` reasoning unboundedly in latency-sensitive products.

### After-response sync hook

After the model produces a response and the application has accepted it:

- Add the user message if it was not already stored.
- Add the assistant response.
- Store tool or subagent outputs only when they are useful for future memory.
- Do not mark local sync complete until the Honcho API call succeeds.

### Migration hook

When enabling Honcho for an existing bot or app:

- If local history exists and the Honcho session is empty, upload a formatted
  transcript or replay messages in chronological batches.
- Use `session.upload_file()` for document-like history and `add_messages()` for
  already structured turns.
- Archive or mark local files after successful import, not before.
- Make migration idempotent by checking existing messages or metadata.

## Conceptual patterns by integration type

### Coding-agent memory

- Use one workspace shared across compatible coding-agent integrations when the
  same user's memory should transfer across tools.
- Use a session ID that represents the project, repository, branch, or task
  scope rather than a new session for every assistant turn.
- Record exact user requests and final assistant answers; omit internal scratch
  unless it is useful durable context.

### Chatbots and customer support

- Use one peer per user account and one assistant peer per bot persona.
- Session granularity is usually one support ticket, channel thread, or chat
  conversation.
- Retrieve `session.context` before each response; use `chat` only for deeper
  personalization or intent questions.

### Multi-agent systems

- Model each agent as a peer if its behavior or beliefs matter.
- Use `target`/`peer_perspective` to ask what one agent knows about another.
- Keep session peers complete; missing peers can prevent desired observations.

### Data ingestion jobs

- Keep ingestion and chat in the same workspace if the chat agent should use the
  imported data.
- Map source records to sessions that preserve natural context: email threads,
  meetings, documents, or ticket histories.
- Preserve timestamps and source identifiers in metadata.

## Verification checklist

- The app still starts with Honcho disabled.
- If the SDK is optional, missing package produces a clear warning and no crash.
- With credentials set, peer/session creation is idempotent.
- Message sync happens after every accepted exchange.
- `get_session_context` or `session.context` returns recent messages promptly.
- Dialectic `chat` returns a reasoned answer after enough message history exists.
- Queue status or webhooks are used only as readiness hints, not as the sole
  source of truth.
