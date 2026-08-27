# Search UI

## When to read this

Read this before changing the collection search box, search tier selection, filters, streaming trace display, result rendering, search usage limits, or generated API-code snippets.

For backend endpoint contracts and schema details, read sibling [backend-api](../../backend-api/SKILL.md) as the authoritative API-shape reference.

## Component ownership

- `Search` owns dashboard-level orchestration for one collection readable ID.
- `SearchBox` owns query entry, tier selection, filter controls, usage gating, request construction, cancellation, and API-code snippets.
- `SearchResponse` owns trace/entity/raw result rendering, copy behavior, pagination, truncation, and streamed agentic event display.

`CollectionDetailView` passes the collection `readable_id` into `Search`. Search is disabled when the collection has no connected source connections.

## Search tiers

The UI exposes three tiers and maps them directly to backend routes:

| Tier | Route | Response style | Key body fields | UI notes |
| --- | --- | --- | --- | --- |
| `instant` | `POST /collections/{collection}/search/instant` | JSON/raw results | `query`, `retrieval_strategy`, optional `filter` | Retrieval strategy selector: `semantic`, `hybrid`, or `keyword`; trace hidden. |
| `classic` | `POST /collections/{collection}/search/classic` | JSON/raw results | `query`, optional `filter` | Default tier; trace hidden. |
| `agentic` | `POST /collections/{collection}/search/agentic/stream` | streamed frames from response body | `query`, `thinking`, optional `filter` | Shows trace; thinking toggle; cancel aborts the request. |

`Search` defaults to the `classic` tier. Agentic always reports a completion-style response to the parent; instant and classic report raw-style responses.

## Filters

The filter builder state is shared across tiers. Before sending a request, `SearchBox` converts UI filter groups with `toBackendFilterGroups()` and includes `filter` only when at least one backend filter group exists.

`SearchResponse` formats filter conditions in traces with shortened labels for common metadata fields and readable symbols for operators such as `equals`, `contains`, `greater_than`, and `in`.

## Usage gating by tier

`SearchBox` checks both usage actions on mount and after search/cancel:

- `GET /usage/check-action?action=queries`
- `GET /usage/check-action?action=tokens`

Tier blocking is split:

- Instant and classic are blocked by the `queries` action.
- Agentic is blocked by the `tokens` action.

If the currently selected tier becomes blocked and the other family is still allowed, the component auto-selects an unblocked tier. If both are blocked, the current tier remains selected but the query input/send control is disabled.

Tooltips explain `usage_limit_exceeded` and `payment_required`, with billing/settings links. If usage checks fail, the UI defaults to not blocking the user; the backend remains authoritative.

## Request lifecycle

On send:

1. Ignore empty query, missing collection, active request, disabled UI, active usage check, or blocked tier.
2. Abort any prior request.
3. Reset transient issue state and allocate a new sequence number.
4. Build the request body and tier-specific URL.
5. Call `apiClient.post()` with an `AbortSignal`.
6. For instant/classic, parse JSON and emit `{ results, responseTime }`.
7. For agentic, read `response.body` as text chunks and parse `data:` frames separated by blank lines.

Error handling:

- `422` responses attempt to extract structured validation messages and surface them as non-transient errors.
- Other failed responses try `detail` or `message` from JSON/text and surface a non-transient error.
- Aborts are ignored as failures and emit cancellation state.
- Unexpected request/stream failures are treated as transient and show a generic retry message.

## Agentic streamed events

Agentic parsing recognizes event objects such as:

- `started`: captures `request_id` and updates stream state.
- `thinking`: displayed in trace as streamed thoughts and optional token diagnostics.
- `tool_call`: displayed with compact labels for search/read/collect/remove/count/navigation/review tools.
- `reranking`: displays rerank counts, first results, scores, and duration.
- `error`: sets a non-transient search error.
- `done`: emits final `results` and response time.
- local `cancelled`: emitted by the UI when an abort is requested.

Trace rendering intentionally distinguishes self-corrected invalid tool calls from real search failures.

## Response panel behavior

`SearchResponse` renders only while a search is active or a response exists.

Tabs:

- `Trace`: shown only when `showTrace` is true, currently agentic search.
- `Entities`: result cards with load-more pagination.
- `Raw`: JSON view with syntax highlighting when small enough.

State details:

- The response card expanded/collapsed state is persisted in `localStorage` as `searchResponse-expanded`.
- Entity display starts with 25 results and loads 25 more per click.
- Raw JSON truncates after 500 lines until the user loads the remaining output; very large JSON falls back to plain text.
- Copy uses `navigator.clipboard` for trace text, raw response JSON, or entity JSON depending on the active tab.

## API-code snippet modal

The code button in `SearchBox` opens a snippet modal. It fetches `/api-keys` on mount and uses the first available `decrypted_key` when present; otherwise it shows `YOUR_API_KEY`.

Snippet generation uses the collection readable ID, current query, selected tier, retrieval strategy, thinking flag, and backend filter groups.

If API-key behavior changes, update this snippet path together with the API key settings/dashboard cards.

## Change checklist

- Keep tier-to-route mapping explicit and aligned with backend search routes.
- Preserve the split between query limits and token limits.
- Recheck usage after search completion and cancellation.
- Do not show trace for instant/classic unless those routes begin emitting useful events.
- Keep agentic stream parsing tolerant of unknown event types.
- Cross-check filter body shape with the backend API sub-skill before changing filter serialization.
