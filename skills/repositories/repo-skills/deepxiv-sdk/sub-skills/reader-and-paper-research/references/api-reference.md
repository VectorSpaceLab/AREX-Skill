# Reader API reference

This reference describes the public `Reader` methods exported by
`deepxiv_sdk.__init__` at package version 1.0.0. The installed signatures are the
source of truth; do not infer extra keyword arguments from old examples.

## Construction and exported errors

```python
from deepxiv_sdk import (
    Reader, agent_search_sources, APIError, BadRequestError,
    AuthenticationError, RateLimitError, NotFoundError, ServerError,
)

reader = Reader(
    token=None,
    base_url="https://data.rag.ac.cn",
    timeout=60,
    max_retries=3,
    retry_delay=1.0,
)
```

The constructor strips trailing `/` from `base_url`, then exposes:

- `arxiv_endpoint = <base_url>/arxiv/`
- `pmc_endpoint = <base_url>/pmc/`
- `agent_search_endpoints["arxiv"] = <base_url>/arxiv/agent/search`
- `agent_search_endpoints["web"] = <base_url>/web/agent/search`
- `token`, `timeout`, `max_retries`, and `retry_delay` as attributes.

`Reader` itself does not make a request during construction. The token is sent as
an `Authorization: Bearer <token>` header by ordinary `_make_request` calls and
agentic POST calls. `search` and `social_impact` also put the token in query
parameters for backend compatibility; never log those request parameters.

The exception hierarchy is:

```text
APIError
├── AuthenticationError   # 401; also 403 agentic access gate
├── BadRequestError       # 400 or 422 agentic validation rejection
├── RateLimitError        # 429
├── NotFoundError         # 404
└── ServerError           # 5xx
```

## Hosted agentic search

### `agent_search`

```python
Reader.agent_search(
    self, query: str, source: str = "arxiv", effort: str = "default",
    verbose: bool = False, max_answer_tokens: int = 4096,
    language: str | None = None, top_k: int | None = None,
    search_type: str | None = None, gl: str | None = None,
    hl: str | None = None, timeout: int | None = None,
) -> dict[str, Any]
```

This performs a blocking `POST` to `<base_url>/{arxiv|web}/agent/search` with
`stream_answer=False` and `verbose` as supplied. The request timeout defaults to
`Reader.AGENT_SEARCH_TIMEOUT` (180 seconds), not the constructor's ordinary
`timeout`. It does not use the ordinary retry policy.

The normal response is shaped like:

```python
{
    "status": "success",
    "answer": "... [arXiv:2409.05591] ...",
    "sources": [...],
    "stats": {"answer_truncated": False, ...},
    "quota": {"tier": "...", "used": ..., "remaining": ...},
    # "trace": [...] only when the backend includes it for verbose=True
}
```

The service may include additional fields. Empty successful bodies become `{}`.
Do not assume `answer`, `stats`, or `quota` exists when mocking, handling an
unusual response, or recovering from a partial service result; use `.get` until
the shape is checked. Before accepting an answer as complete, require
`result.get("stats", {}).get("answer_truncated") is False` (or an explicitly
present false value).

### `agent_search_stream`

```python
Reader.agent_search_stream(
    self, query: str, source: str = "arxiv", effort: str = "default",
    verbose: bool = False, stream_answer: bool = True,
    max_answer_tokens: int = 4096, language: str | None = None,
    top_k: int | None = None, search_type: str | None = None,
    gl: str | None = None, hl: str | None = None,
    timeout: int | None = None,
) -> Iterator[dict[str, Any]]
```

This performs a streaming `POST` to `<base_url>/{arxiv|web}/agent/search/stream`
with `stream=True` and yields each valid, parsed NDJSON object. Blank lines and
malformed JSON lines are skipped. The SDK does not validate the event schema.
The expected protocol is:

| `event` | Common fields and handling |
| --- | --- |
| `billing` | quota fields; current backends may expose `tier`, `used`, `remaining`, and/or cost fields |
| `start` | run/model/effort metadata |
| `answer_start` | timing such as `elapsed_ms` |
| `answer_delta` | append `text`; this is final-answer text only |
| `answer` | one complete answer when `stream_answer=False` |
| `sources` | `papers` for arXiv or `pages` for web |
| `done` | timing plus `answer_truncated`; completion gate |
| `tool_call`, `tool_result`, `thinking`, `warning` | optional when `verbose=True`; keep narration separate from answer |
| `error` | `stage` and `message`; yielded instead of raised |

A safe collector concatenates every `answer_delta["text"]`, also accepts an
`answer["text"]`/`answer["answer"]` shape only if the actual event supplies it,
records `sources`, and refuses to publish a final result until `done` says
`answer_truncated` is false. In the current documented protocol the blocking
response carries `answer` as a string; a stream with `stream_answer=False` carries
one `answer` event.

Transport errors are raised as `APIError`; HTTP status errors use the exception
mapping below. An `error` event is not converted into an exception by the SDK,
which matters when output has already been displayed. The two agentic methods do
not auto-retry: a retry would spend another agentic quota unit and restart the
run.

### Agent argument validation and payloads

Validation occurs before `requests.post`, so invalid calls do not spend a quota
unit. The accepted values and backend-specific behavior are:

| Argument | Exact client-side rule |
| --- | --- |
| `source` | `"arxiv"` or `"web"` |
| `query` | nonblank after stripping; at most 2,000 characters; the stripped value is sent |
| `effort` | `"default"`, `"high"`, or `"xhigh"` |
| `max_answer_tokens` | inclusive range 256–16,384 |
| `language` | included only when truthy |
| `top_k` | arXiv only, defaults to 10, inclusive range 1–30 |
| `search_type` | web only, defaults to `"search"`; `"search"`, `"scholar"`, `"news"`, or `"images"` |
| `gl`, `hl` | web only and included when truthy; locale is otherwise left to the service |

Passing `top_k` to web, or `search_type`, `gl`, or `hl` to arXiv, raises
`ValueError`; unsupported backend flags are not silently dropped. The payload
always contains `query`, `effort`, `verbose`, `stream_answer`, and
`max_answer_tokens`, plus applicable options. The backend may switch web locale
for Chinese queries when `gl`/`hl` are omitted; answers normally follow the query
language unless `language` is set.

### Agent HTTP failures

`401` raises `AuthenticationError` for a missing/invalid/expired key. `403` also
raises `AuthenticationError`, but means a valid SDK/auto-registered key lacks
agentic access: obtain a registered account key from the service's registration
page and configure it through the user's normal credential mechanism. `400` and
`422` raise `BadRequestError` (FastAPI validation details are included when
available), `429` raises `RateLimitError` for the separate agentic pool, `5xx`
raises `ServerError`, and other HTTP failures raise `APIError`.

## Source normalization and IDs

```python
from deepxiv_sdk import agent_search_sources
items = agent_search_sources(event_or_result)
```

The helper checks `papers`, then `pages`, then `sources`, returning the first
non-`None` value or `[]`. Thus it normalizes a streaming arXiv `sources` event, a
streaming web event, and a blocking result without changing item dictionaries.

- arXiv entries normally expose `arxiv_id`, `title`, and `url`.
- Web entries normally expose `url`, `title`, and boolean `read`.
- Blocking agent results use `sources`; do not assume they use `papers`.
- The source list is the retrieval set, not necessarily the citation set. Match
  arXiv IDs (or web URLs) that occur in the answer before calling an item cited.
  Keep retrieved-but-uncited items separately.

## Progressive arXiv access

All these methods issue an ordinary GET through the arXiv endpoint and return an
empty fallback for a successful empty result. Each ID argument must be nonblank;
these methods do not client-side validate the full ID syntax.

| Method and exact signature | Request/return behavior |
| --- | --- |
| `search(query, size=10, offset=0, source="arxiv", categories=None, authors=None, orgs=None, venue=None, venues=None, venue_year=None, min_citation=None, date_search_type=None, date_str=None, date_from=None, date_to=None, use_fine_rerank=False, top_k=None)` | Unified retrieve. Returns `{status, total_count, result}`; result IDs are `arxiv_id`, `biorxiv_id`, or `medrxiv_id` according to `source`. `top_k` overrides `size`. |
| `head(arxiv_id)` | Metadata and structure: title, abstract, authors, sections, token count, categories, publication date. Returns a dictionary. |
| `brief(arxiv_id)` | Concise metadata such as title, TLDR, keywords, publication date, citations, PDF URL, and optional GitHub URL. Returns a dictionary. |
| `section(arxiv_id, section_name)` | Case-insensitive exact or partial section match, then returns the matched section's `content` string. Missing section raises `ValueError`. |
| `preview(arxiv_id)` | Returns a preview dictionary, documented as the first 10,000 characters, with `content`, `is_truncated`, and `total_characters` when supplied. |
| `raw(arxiv_id)` | Returns the full paper markdown string from the `raw` field. Potentially large. |
| `json(arxiv_id)` | Returns the complete structured paper dictionary. Potentially large. |
| `markdown(arxiv_id)` | No request; returns `https://arxiv.org/html/<arxiv_id>` after nonblank validation. |

The `head` documentation describes `sections` as a list of section information,
but service/test fixtures may expose a mapping-like shape as well. Inspect the
returned value before iterating it; do not assume either `.items()` or only list
entries. `section` calls `head` again and extracts names from iterable entries (or
stringifies them) to resolve the server's canonical section name. A section name
such as `"method"` can match a longer section name, case-insensitively. The old
example's `.items()` loop is not a universal API contract.

## Search validation, filters, and pagination

`search` rejects blank queries, sources outside `arxiv`, `biorxiv`, and `medrxiv`,
`effective_top_k` outside 1–100, and offsets outside 0–10,000. Although the
method docstring describes a 500-character query maximum, the current client
only checks nonblank input; the service remains authoritative for any length
limit. `query` is not stripped before being sent.

The request uses `type="retrieve"`, `query`, `source`, `top_k`, `offset`, and
`use_fine_rerank="true"` or `"false"`; `token` is included as a query parameter
when present. Nonempty list filters are sent as repeated request keys:
`categories`, `authors`, and `orgs`. `venue` accepts one string or a list;
`venues` is a plural alias and both are merged under repeated `venue` keys.
`venue_year` and `min_citation` are passed when not `None`. Venue aliases are
matched server-side and are best-effort.

Date forms are:

- `date_search_type="between" | "exact" | "after" | "before"`, paired with
  `date_str`;
- `date_str` is a single date string except `between`, where it must be a
  two-element list/tuple;
- `date_from` and `date_to` are convenience forms: both map to `between`, only
  `date_from` maps to `after`, and only `date_to` maps to `before`;
- a `date_str` without a date type, a type without a date, an invalid type, or a
  non-two-element `between` value raises `ValueError`.

No date-format validation is done client-side. A successful empty/falsey response
is normalized to `{"status": "success", "total_count": 0, "result": []}`.
Paginate with `offset += page_size` while retaining the returned `total_count`;
stop on an empty `result` or when the collected count reaches the desired bound.

## Other Reader methods

### PMC

```python
Reader.pmc_head(pmc_id: str) -> dict[str, Any]
Reader.pmc_full(pmc_id: str) -> dict[str, Any]
Reader.pmc_json(pmc_id: str) -> dict[str, Any]  # exact alias of pmc_full
```

Each validates a nonblank ID and calls `<base_url>/pmc/` with `pmc_id` and
`type="head"` or `type="json"`. `pmc_head` returns metadata (title, abstract,
authors, categories, publication date, and DOI when available); the full methods
return structured complete data.

### bioRxiv and medRxiv

```python
Reader.biomed_search(
    query: str, source: str = "biorxiv", top_k: int = 10,
    authors: list[str] | None = None, orgs: list[str] | None = None,
    date_search_type: str | None = None, date_str: Any = None,
    use_fine_rerank: bool = False,
) -> dict[str, Any]

Reader.biomed_data(
    source_id: str, source: str = "biorxiv", data_type: str = "metadata",
    section_names: list[str] | None = None, roc_num: int | None = None,
    fields: str | None = None,
) -> dict[str, Any]
```

`biomed_search` only accepts `source="biorxiv"` or `"medrxiv"` and delegates to
`search`, so its result shape is `{status, total_count, result}` and returned IDs
are source-specific. `source_id` for `biomed_data` is a DOI-like source ID, not
an arXiv ID. `data_type` must be `metadata`, `section`, or `roc`; section names
are sent comma-separated, and optional `roc_num` and comma-separated `fields`
are passed through. The request is `GET <base_url>/<source>/data`.

### Trending and social impact

```python
Reader.trending(days: int = 7, limit: int = 30) -> dict[str, Any]
Reader.social_impact(arxiv_id: str) -> dict[str, Any] | None
```

`trending` validates `days` 1–30 and `limit` 1–100, calls the fixed trending
service endpoint, unwraps a nested `data` object, and normally returns
`papers`, `total`, `days`, and `generated_at`. If the response has no `data`, it
returns `{"papers": [], "total": 0}`. The endpoint is documented as not
requiring a token.

`social_impact` validates a nonblank arXiv ID and requires a token before making
a request. It calls `<base_url>/arxiv/trending_signal` with `arxiv_id` and the
token query parameter. It returns metrics such as views, likes, tweets, replies,
first/last seen dates, and ID when data exists; a 404 or empty successful body
becomes `None`. Other API errors propagate.

## Ordinary request retries

Non-agentic GET calls use the constructor's `timeout`, and `_make_request` retries
only `requests` timeout and connection exceptions. The wait is
`retry_delay * 2**retry_count`: with defaults, retries wait 1, 2, and 4 seconds
and there are four total attempts including the first. HTTP 400/401/404/429/5xx,
JSON decoding failures, and other request failures are raised rather than
retried. `max_retries=0` disables retry attempts. This retry policy does not
apply to either agentic method.
