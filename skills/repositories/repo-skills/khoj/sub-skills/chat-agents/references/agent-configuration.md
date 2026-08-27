# Agent Configuration

Khoj mounts the agent router at `/api/agents`. Public reads can be unauthenticated where the route allows it, but create/update/delete and hidden-agent endpoints require authentication.

## Agent Data Model

Agents are stored with:

- `name`: display name.
- `persona`: API field mapped to the database `personality` prompt.
- `privacy_level`: one of `public`, `private`, or `protected`.
- `icon`: style icon value stored as `style_icon`.
- `color`: style color value stored as `style_color`.
- `chat_model`: user-facing friendly model name on API input/output; internally converted to a `ChatModel.name` when saved.
- `files`: selected filenames from the creator's existing indexed knowledge base.
- `input_tools`: optional list of allowed data-source tools for automatic/default chat routing.
- `output_modes`: optional list of allowed non-text output modes.
- `slug`: stable identifier. New agents generate a slug from the name if one is not supplied.
- `is_hidden`: true for private per-conversation agents that should not appear in normal agent lists.

The default agent has slug `khoj`, name `Khoj`, public privacy, admin management, and empty `input_tools`/`output_modes`. Empty tool/output lists mean the default chat router can consider all currently available options.

## Privacy and Accessibility

- `public`: accessible to all users. Normal public listing only includes admin-managed public agents plus the current user's non-hidden agents.
- `private`: accessible to the creator. Private prompt safety checks are run in lax mode.
- `protected`: readable through the readonly slug endpoint and general accessibility checks, but normal creator-scoped mutation lookup uses public-or-creator access. Treat protected as a broader-read, narrower-management visibility level.
- Hidden agents are private, associated with one conversation, and omitted from the normal all-agents list.

When a conversation history is returned, private agent metadata is hidden from non-creators. Public shared conversation history substitutes the default agent metadata for inaccessible hidden private agents.

## Create or Update Agent Body

`POST /api/agents` creates or upserts an agent for the authenticated user. `PATCH /api/agents` updates an existing agent selected by `slug`.

`ModifyAgentBody` fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | yes | Display name. |
| `persona` | string | yes | System/personality prompt. New public/protected prompts are safety-checked more strictly than private prompts. |
| `privacy_level` | string | yes | `public`, `private`, or `protected`. |
| `icon` | string | yes | Must align with available style icon choices. |
| `color` | string | yes | Must align with available style color choices. |
| `chat_model` | string | yes | Friendly chat model name looked up through configured chat models. |
| `files` | list of strings | optional | Existing user file names/paths to copy into the agent knowledge base. Defaults to `[]`. |
| `input_tools` | list of strings | optional | Agent-allowed input sources. Defaults to `[]`. |
| `output_modes` | list of strings | optional | Agent-allowed non-text outputs. Defaults to `[]`. |
| `slug` | string or null | optional | Existing slug for update or caller-chosen slug for upsert. |
| `is_hidden` | boolean | optional | Usually false for user-visible agents. |

Create/update responses include `slug`, `name`, `persona`, `creator`, `managed_by_admin`, `color`, `icon`, `privacy_level`, `chat_model`, `files`, `input_tools`, `output_modes`, and sometimes `is_hidden`.

## Hidden Agent Body

Hidden agents are private per-conversation agents for internal/custom conversation behavior.

`ModifyHiddenAgentBody` fields:

| Field | Type | Notes |
| --- | --- | --- |
| `slug` | string or null | Existing hidden agent slug for patch; optional on create. |
| `persona` | string or null | Hidden agent prompt. |
| `chat_model` | string or null | Friendly chat model name. If unavailable to the user, update falls back to the default chat model. |
| `input_tools` | list of strings | Defaults to `[]`. |
| `output_modes` | list of strings | Defaults to `[]`. |

Endpoints:

- `POST /api/agents/hidden?conversation_id=<id>` creates a hidden private agent and attaches it to a conversation that has no custom agent or only the default agent.
- `PATCH /api/agents/hidden` updates an existing hidden/private agent by `slug`.
- Hidden-agent responses return `slug`, `name`, `persona`, `creator`, `chat_model`, `input_tools`, and `output_modes`.

If `POST /hidden` targets a missing conversation, it returns 404. If the conversation already has a non-default agent, it returns 400 and instructs callers to use `PATCH`.

## Agent Endpoints

- `GET /api/agents` returns accessible agents, with the default agent first when present, then recent-conversation agents, then shuffled unused agents. Authenticated users see admin-managed public agents plus their own non-hidden agents; unauthenticated users see public admin-managed agents.
- `GET /api/agents/options` returns descriptions for valid agent `input_tools` and `output_modes`.
- `GET /api/agents/{agent_slug}` returns a readonly public/protected/creator-accessible agent packet.
- `GET /api/agents/conversation?conversation_id=<id>` returns the agent bound to a conversation, falling back to the default agent. If the user lacks the subscription tier required by the model, `chat_model` is returned as `null`.
- `DELETE /api/agents/{agent_slug}` deletes a creator-owned agent and its agent-specific entries; non-existent or inaccessible agents return 404.
- `POST /api/agents` creates/upserts a normal agent.
- `PATCH /api/agents` updates a normal agent selected by `slug`.

## Tool and Output Options

Agent option enums intentionally differ from all chat slash commands.

Input tools currently exposed by `Agent.InputToolOptions`:

- `general`: agent may use general model knowledge.
- `online`: agent may search online when web search is enabled.
- `notes`: agent may use the user's or agent's knowledge base.
- `webpage`: agent may read specific webpage URLs.
- `code`: agent may run sandboxed Python when a sandbox is enabled.

Output modes currently exposed by `Agent.OutputModeOptions`:

- `image`: agent may generate creative images when a text-to-image model is configured.
- `diagram`: agent may generate Mermaid.js diagram output.

`research` and `operator` are chat/research commands in the conversation command enum, but they are not currently part of the agent input tool choices returned by `/api/agents/options`. Do not put them into `input_tools` unless the model enum has changed.

## File Knowledge Bases

When an agent is updated with `files`, Khoj performs an atomic replacement of that agent's file knowledge base:

1. Delete existing `FileObject` and `Entry` rows for the agent.
2. Copy matching file objects from the creator's user-level indexed files where `agent=None`.
3. Copy matching entries from the creator's user-level indexed entries into agent-scoped entries.
4. Bulk create new file objects and entries.

Consequences:

- `files` must refer to content already indexed for the creator; the agent API does not parse or upload files itself.
- For upload/sync/parsing problems, route to `content-indexing` before retrying agent file selection.
- For agent-specific search result behavior, route ranking/filter internals to `search-retrieval` after confirming the agent has copied entries.
- Concurrent or large updates should be treated as replacement operations; tests assert atomicity so partial file syncs are bugs.

## Chat Model Selection

Normal agent create/update accepts a friendly chat model name, resolves it to a configured `ChatModel`, and checks subscription access:

- If the requester is subscribed or the selected model has free price tier, Khoj saves that selected model.
- If not, the route passes no selected model into the adapter; the adapter falls back to the user's/default chat model.
- The default agent dynamically uses the user's/default chat model instead of its stored model.
- A non-default agent with a deleted/unset chat model falls back to the overall default model and logs a warning.

Model setup itself is an admin/deployment concern; use `deployment-api` for creating model providers, API keys, base URLs, and server chat settings.

## Prompt Safety

Agent create/update checks prompt safety before writing:

- Public/protected-style prompts are checked with the stricter safety prompt.
- Private prompts are checked with lax mode.
- If the checker returns unsafe, the API returns 400 with the reason.
- Hidden agents are created through the adapter path and should still be treated as untrusted user prompt input in any custom changes.

## Practical Payload Example

A private agent with restricted data sources, image/diagram outputs, and file knowledge uses a body like:

```json
{
  "name": "Research Designer",
  "persona": "Help synthesize my design notes and cite relevant files before answering.",
  "privacy_level": "private",
  "icon": "Lightbulb",
  "color": "blue",
  "chat_model": "gpt-4o-mini",
  "files": ["design-notes.md", "research/brief.md"],
  "input_tools": ["notes", "online", "webpage", "code"],
  "output_modes": ["image", "diagram"],
  "slug": "research-designer",
  "is_hidden": false
}
```

Before blaming the agent API for missing knowledge, verify those filenames exist in the creator's indexed content. Before blaming output mode selection, verify the required image/diagram/model services are configured.
