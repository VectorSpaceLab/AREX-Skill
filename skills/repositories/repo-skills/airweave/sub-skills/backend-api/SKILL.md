---
name: backend-api
description: "Operates Airweave's backend API surface for search tiers,
  collections, source connections, Connect sessions, browse-tree selection,
  sources, webhooks, usage checks, source rate limits, and streaming search
  debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Backend API

Use this sub-skill when an Airweave task touches the FastAPI service as a user-facing API: collection search, collection CRUD, source-connection creation/auth/sync jobs, Connect sessions, browse-tree node selection, source discovery, auth-provider connections, API keys, usage checks, source rate limits, webhook subscriptions/messages, or local debugging of agentic search streams.

## Route to the right reference

- Read [references/api-reference.md](references/api-reference.md) for endpoint tables, request bodies, response shapes, filters, auth/header rules, and status/error conventions.
- Read [references/workflows.md](references/workflows.md) for end-to-end recipes: create-and-search, search tier selection/cancel/retry, OAuth claim-token verification, Connect sessions, browse-tree selection, webhooks, and source rate-limit checks.
- Read [references/troubleshooting.md](references/troubleshooting.md) when diagnosing 401/403/404/422/429 errors, search/SSE stalls, usage blocks, OAuth pending states, Connect mode failures, webhook delivery problems, or source rate-limit surprises.
- Use [scripts/agentic_search_stream.py](scripts/agentic_search_stream.py) as the bundled CLI viewer for `POST /collections/{readable_id}/search/agentic/stream` when a local backend is running.
- Cross-link to sibling [source-connectors](../source-connectors/SKILL.md) for connector registry semantics, source capability fields, browse-tree source implementation behavior, and per-source config/auth details.
- Cross-link to sibling [connect-widget](../connect-widget/SKILL.md) for iframe messaging, SDK/session-mode UX, OAuth popup handling, and parent-window token exchange details.

## Operating rules

1. Use root-relative backend paths such as `/collections` and `/source-connections`; do not add an `/api/v1` prefix to dashboard/client code.
2. Use collection `readable_id` values in collection search and collection CRUD paths. Use UUIDs for source-connection IDs, sync job IDs, webhook subscription/message IDs, and Connect session IDs.
3. Preserve headers. Regular backend calls need the normal user/API auth context plus `X-Organization-ID` when operating in a selected organization. Connect session calls use `Authorization: Bearer <session_token>` and are not ordinary API-key calls.
4. Treat usage checks as preflight hints and backend checks as authoritative. Instant/classic/browse/legacy search consume `queries`; agentic and agentic stream consume `tokens`; source creation and sync creation also check their usage actions.
5. Keep the search tiers distinct: instant is direct retrieval, classic asks an LLM to plan before retrieval, agentic runs a tool-using loop, and agentic streaming returns Server-Sent Events.
6. Do not mix filter dialects. V2 search tiers use `filter: [{conditions: [...]}]`; the legacy search route accepts a Qdrant-style dict such as `{must: [...]}`.
7. Preserve the OAuth claim-token contract: keep the `claim_token` from source-connection creation until `verify-oauth` succeeds; removing it earlier leaves the flow unrecoverable for the user without re-initiation.
8. Keep destructive lifecycle operations explicit. Deleting a collection or source connection cascades/cleans synced data; cancelling a sync transitions through `cancelling` before `cancelled`.
9. Keep Connect widget iframe internals and source implementation internals out of this sub-skill. Route iframe messaging to `connect-widget`; route source class/config/browse-tree implementation details to `source-connectors`.
10. Do not depend on the original repository checkout for runtime guidance. Use the bundled references and helper script here.

## Quick decision map

| User intent | Start here | Notes |
| --- | --- | --- |
| "Which search endpoint/body should I use?" | `api-reference.md` → Search v2 and legacy search | Check tier, filter dialect, and usage action. |
| "Search stream hangs or shows wrong events" | `troubleshooting.md` → SSE/search stream | Confirm current `/collections/{id}/search/agentic/stream` path and event names. |
| "Create collection and index a source" | `workflows.md` → Collection to searchable data | Covers collection, source connection, sync polling, and cleanup. |
| "OAuth source is stuck pending" | `workflows.md` and `troubleshooting.md` → OAuth claim token | Verify before clearing stored claim token; re-initiate when needed. |
| "Embed Airweave Connect" | `workflows.md` → Connect session backend flow, then `connect-widget` | Backend owns session/source-connection endpoints; widget owns iframe details. |
| "Select folders/items before sync" | `workflows.md` → Browse-tree selection, then `source-connectors` | Backend owns routes; connector skill owns source capability semantics. |
| "Subscribe to events" | `api-reference.md` and `workflows.md` → Webhooks | Include event types, secret handling, attempts, recovery. |
| "Why is a source sync slow/throttled?" | `api-reference.md` → source rate limits, then `troubleshooting.md` | Check feature flag, source `rate_limit_level`, and configured limits. |

## Validation anchors for later verification

Later whole-skill verification should exercise representative native backend smoke coverage for search v2, legacy search, filters, agentic SSE, collections, Connect sessions, source connections, webhooks, source listing, rate limiting, sync run/cancel lifecycle, entity definitions, and storage-backed sync. Credentialed provider flows should remain opt-in unless the required external accounts and secrets are available.
