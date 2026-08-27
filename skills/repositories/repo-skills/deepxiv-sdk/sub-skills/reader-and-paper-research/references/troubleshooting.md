# Reader troubleshooting

Use the smallest recovery action that addresses the observed failure. Do not
retry a quota-billed agentic call automatically, and do not put tokens in source,
logs, error reports, or command arguments that may be recorded.

## Before a live request

Run the no-network helper first:

```text
python /path/to/reader-and-paper-research/scripts/reader_probe.py
```

It should report the package version, constructor endpoint summary, and passing
validation cases without contacting a service. From a Python shell, confirm the
import surface with:

```python
from deepxiv_sdk import Reader, agent_search_sources
reader = Reader()
print(reader.base_url, reader.timeout, reader.max_retries)
```

If importing `Reader` fails, use the root route's installation guidance rather
than trying CLI commands in this route. Local model/LangGraph import problems
belong to [optional local agent](../../optional-local-agent/SKILL.md).

## Authentication and quota

### Agentic `AuthenticationError`

- `401`: the key is invalid, expired, or missing for a protected service. Supply
  a valid user-provided token through runtime configuration.
- `403`: the token may work for ordinary SDK calls but is not an agentic-enabled
  registered account key. Obtain the registered key at
  `https://data.rag.ac.cn/register` and replace the runtime token. The
  auto-registered SDK token is not sufficient for hosted agentic search.

Do not “fix” a 403 by retrying the same call; it will not change authorization and
may consume a call if the backend reaches billing. Ordinary `search`, paper
reading, PMC, and biomedical calls use the general service path and have separate
availability/quota semantics.

### `RateLimitError`

Agentic `429` is an exhausted agentic quota pool, separate from the general Reader
pool. The SDK does not retry either agentic method. Stop, report the remaining
quota if the response supplied it, and either wait for reset, narrow future work,
or use an account tier appropriate to the task. A general GET `429` is mapped to
the same exception class but has the ordinary daily-limit message.

## Agent validation and response failures

A `ValueError` before a POST means local validation rejected the call and no
agentic quota should have been spent. Check these common mismatches:

- query is blank or over 2,000 characters;
- effort is not `default`, `high`, or `xhigh`;
- `max_answer_tokens` is outside 256–16,384;
- arXiv `top_k` is outside 1–30;
- web uses `top_k`, or arXiv uses `search_type`, `gl`, or `hl`;
- web `search_type` is not `search`, `scholar`, `news`, or `images`.

A service-side `BadRequestError` is 400/422. Read its validation detail, correct
the payload, and submit a new bounded request. Do not pass old CLI flags or
removed search weighting parameters to `Reader.search`.

A `ServerError` is a 5xx service response. A transport `APIError` may indicate a
network failure, timeout, malformed JSON, or an agentic request failure. For an
agentic timeout, try a narrower query, `effort="default"`, or an explicit smaller
scope; increasing the constructor's ordinary `timeout` does not alter the
agentic default unless `timeout=` is passed to the agentic method.

## Streaming hazards

The stream parser skips blank and malformed NDJSON lines. This is intentionally
lenient, so a missing event may be a backend/proxy problem rather than a clean
success. Keep flags:

```python
saw_done = False
saw_error = False
truncated = False
```

- `error` is yielded, not raised. A partial answer may already be in `chunks`;
  label it partial and do not publish it as final.
- `done.answer_truncated` must be explicitly false before final publication.
- If no `done` arrives, treat the run as incomplete even if deltas were received.
- `answer_delta` is final answer text; do not merge `thinking` or tool narration
  into it.
- A stream with `stream_answer=False` has one `answer` event rather than deltas;
  support both forms when writing a generic collector.

The bundled stream adapter reports event/error/truncation state to stderr and
uses a nonzero exit status for incomplete output. It never prints the token it
uses from `DEEPXIV_TOKEN`.

## Source-quality mistakes

### “Retrieved” was reported as “cited”

`agent_search_sources(result)` returns the whole retrieval set. It does not know
which source was cited. Match `arxiv_id` or URL against the answer and maintain
separate cited and uncited lists. The source set may be larger than the answer's
bibliography.

### Snippet-only web evidence was presented as full reading

For web pages, inspect `page.get("read")`. `True` means the cached body was read;
`False` means only a search snippet was available. Qualify claims based on the
latter, especially current prices, dates, or fine print. The service does not
fetch live pages during hosted agentic search, so a current-page claim may need a
separate user-approved verification step.

### A truncated answer was summarized

For blocking output, check `result["stats"]["answer_truncated"]`; for streams,
check `done["answer_truncated"]`. Raise the answer cap within its range or ask a
narrower follow-up that targets the missing fact. Preserve the original as
incomplete in the research record.

## Search and reading failures

- **Empty `result`:** filters combine. Remove one of the date, citation, venue,
  category, author, or organization constraints; refine the query only after
  verifying that the collection/source is correct.
- **Unexpected result key:** current Reader search uses `result`, not the stale
  `results` key in an older example. Agentic source lists use `sources` in
  blocking responses, `papers` in arXiv stream events, and `pages` in web stream
  events; use the normalization helper.
- **No paper content:** verify the namespace and ID. `head`/`brief`/`section`/
  `raw` take arXiv IDs; PMC methods take PMC IDs; `biomed_data` takes a
  bioRxiv/medRxiv DOI-like ID and a matching `source`.
- **Section not found:** call `head` and use one of its names. `section` supports
  case-insensitive and partial matching, but it still raises `ValueError` when
  no name matches. Read `brief` as a fallback only if a summary is sufficient.
- **Too much content:** stop using `raw`/`json` for screening. Use `brief`, then
  `head`, then one or two sections; `preview` is bounded but can be truncated.
- **Old sample fails:** `preview()` takes only `arxiv_id`; search responses use
  `result`; `head["sections"]` should be consumed according to the returned
  shape, not by assuming a dictionary. Follow the exact API reference here.

## Ordinary GET retry behavior

The constructor's `timeout`, `max_retries`, and `retry_delay` affect ordinary
GET methods only. Timeout and connection errors retry with delays
`retry_delay`, `2*retry_delay`, `4*retry_delay`, and so on, up to the configured
retry count. HTTP 400, 401, 404, 429, and 5xx responses are mapped immediately;
they are not retried. Set `max_retries=0` for a no-retry ordinary probe. If an
ordinary request ends in `APIError`, verify connectivity and the service status,
then decide whether a fresh request is appropriate.

## Endpoint-specific caveats

- `trending` validates days 1–30 and limit 1–100. No-data responses may contain
  only `papers` and `total`, so use `.get` for optional `days` and
  `generated_at`.
- `social_impact` fails locally with `AuthenticationError` when no token is
  supplied; a not-found signal is normal and returns `None`.
- `biomed_search` only accepts `biorxiv` and `medrxiv`; `biomed_data` only accepts
  `metadata`, `section`, and `roc` data types.
- `markdown` only constructs an arXiv HTML URL and does not validate availability
  or fetch the paper.

When reporting an unresolved issue, include method, backend/source, sanitized
validation arguments, exception class/message, whether a `done` event appeared,
and whether truncation was reported. Omit tokens, local paths, and private
runtime identifiers.
