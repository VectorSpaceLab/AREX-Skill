# MCP Server Workflows

Use these workflows when changing or debugging the MCP server package. They describe the runtime tool contracts and the implementation invariants that the offline tests protect.

## Recommended lookup flow

1. Call `search_docs(query, k=5)` to find likely documentation URLs.
2. Call `fetch_doc(uri="...")` on a chosen result to inspect the table of contents, preamble, or full small document.
3. For large documents, call `fetch_doc(uri="...", section="1")` or another returned section ID to retrieve only the needed section.
4. If body-only search terms are missing immediately after startup, hydrate the target page with `fetch_doc` or enable prefetch and allow the background hydration thread to finish.

## `search_docs` contract

Signature: `search_docs(query: str, k: int = 5) -> list[dict[str, object]]`.

Each result dictionary has exactly the public fields below:

| Field | Meaning |
| --- | --- |
| `url` | Documentation URL from the curated catalog. |
| `title` | Display title, preferring the curated `llms.txt` title. |
| `score` | Rounded weighted TF-IDF score. Higher is better within the same query only; do not compare across queries or treat as a probability. |
| `snippet` | Hydrated content preview when available; otherwise the display title fallback. |

Important behavior:

- Returns `[]` when no indexed document matches the query.
- Searches title variants immediately after `llms.txt` catalog load.
- Searches body content only after a page is hydrated by `search_docs`, `fetch_doc`, or background prefetch.
- Hydrates up to five unique top-ranked pages concurrently for snippets.
- If a top result cannot be fetched for a snippet, the result can still be returned with its URL, title, and title fallback snippet.

## `fetch_doc` contract

Signature: `fetch_doc(uri: str = "", section: str = "") -> dict[str, object]`.

Return shape by mode:

| Mode | Trigger | Return shape |
| --- | --- | --- |
| Catalog | `uri` omitted or empty | `{ "urls": [{ "url": str, "title": str }, ...] }` |
| Unsupported URL | non-empty `uri` is not HTTPS on exactly `strandsagents.com` | `{ "error": "only https://strandsagents.com URLs allowed", "url": uri }` |
| Fetch failure | allowed URL cannot be fetched | `{ "error": "fetch failed", "url": uri }` |
| Small document | fetched content is at most 8192 bytes | `{ "url": uri, "title": str, "document_small": true, "reason": "size", "content": str }` |
| No parseable sections | large content has no valid `##` sections | `{ "url": uri, "title": str, "document_small": true, "reason": "no_sections", "content": str }` |
| TOC | large document, no `section` | `{ "url": uri, "title": str, "preamble": str, "sections": [section, ...] }` |
| Section | large document, valid `section` | `{ "url": uri, "title": str, "section_id": str, "section_title": str, "content": str }` |
| Unknown section | large document, invalid `section` | `{ "error": "section '<id>' not found", "url": uri }` |

A TOC `section` object contains only public fields:

```json
{
  "id": "1",
  "level": 2,
  "title": "Section title",
  "summary": "First meaningful paragraph or child fallback",
  "children": [{ "id": "1.1", "title": "Child title" }]
}
```

Internal parser offsets and helper fields are intentionally stripped before tool responses.

## Catalog indexing and hydration lifecycle

1. `ensure_ready()` lazily initializes global cache state.
2. `load_links_only()` parses configured `llms.txt` sources, records curated titles, stores URL placeholders, and indexes title variants with empty content.
3. `ensure_page(url)` fetches and cleans page content, formats the display title, updates the index with body content, then commits the page to cache.
4. The page is left uncached if fetch or indexing fails, so a later call can retry hydration.
5. `STRANDS_MCP_PREFETCH_ALL=1`, `true`, or `yes` starts a daemon thread that attempts to hydrate all known URLs after catalog load.

Concurrency notes:

- The indexer guards `add`, `update_content`, and search snapshots with a lock.
- Cache hydration commits indexing and caching under a cache lock to avoid returning a page whose body terms were not indexed.
- Background prefetch starts once, guarded separately from foreground hydration.
- Search during hydration is eventually consistent: it may see title-only results until the relevant page has finished indexing.

## Section parsing and extraction

- Sections are top-level Markdown `##` headings; headers inside fenced code blocks are ignored.
- Section IDs are one-based strings: `1`, `2`, `3` for top-level sections.
- Child headings below a top-level `##` receive dotted IDs such as `1.1` and `1.2`.
- Extraction supports top-level IDs and one dotted child level. For deeper conceptual nesting, fetch the nearest returned child section and inspect its content.
- Preamble is content before the first valid `##` heading, with the first H1 title stripped when present.
- Section summaries skip code fences, heading lines, bullets, and numbered lists, using the first meaningful paragraph or a child-heading fallback.

## Offline and live test split

Use offline tests for normal server edits:

- Server tool contracts and URL restrictions.
- Index ranking and body-term hydration.
- Cache/prefetch environment-variable behavior.
- Concurrent index/cache invariants.
- Markdown snippet, preamble, TOC, and section extraction.
- Dependency import guardrails.

Live integration tests deliberately fetch `strandsagents.com` catalog/pages and should be run only when network access is permitted and relevant. Skip them for offline CI, constrained environments, or when the change does not touch live fetching behavior.
