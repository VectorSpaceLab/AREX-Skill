# Reader research workflows

These recipes use the Python API, not the `deepxiv` CLI. They are deliberately
bounded: screen cheaply, inspect structure, then read only the evidence needed for
the question.

## 1. Design a hosted agentic question

Use a question that names the object, comparison, metric, and scope. The service
assumes the query is already refined; effort changes gathering rounds, not the
direction of first-round recall.

```python
from deepxiv_sdk import Reader

reader = Reader(token=None)  # supply a registered key through runtime configuration
result = reader.agent_search(
    "Compare speculative decoding speedups on HumanEval for papers from 2024-2025; "
    "report the target model, baseline, and exact speedup with arXiv citations",
    source="arxiv",
    effort="high",
    top_k=10,
    max_answer_tokens=4096,
)

answer = result.get("answer", "")
stats = result.get("stats") or {}
if stats.get("answer_truncated") is not False:
    raise RuntimeError(
        "answer is incomplete or its truncation status is missing; "
        "do not summarize it as complete"
    )
print(answer)
print(result.get("quota", {}).get("remaining"), "agentic calls remaining")
```

Use `default` for a narrow lookup, `high` for a comparison, and `xhigh` for a
survey-like synthesis. Ask explicitly for numbers or the relevant benchmark when
those facts matter. For Chinese queries, the service can rewrite arXiv retrieval
terms and choose a Chinese web locale; use `language` only when overriding the
answer language.

For web research, change `source="web"` and choose one of `search`, `scholar`,
`news`, or `images` with `search_type`. `top_k` is arXiv-only; passing it to web
is a client-side error. Use `gl`/`hl` only for web when a locale must be pinned.

## 2. Stream safely and preserve citations

Streaming is useful when the caller wants early output. It is not a license to
publish before completion: deltas may be followed by an error or a truncation
flag.

```python
from deepxiv_sdk import Reader, agent_search_sources

chunks = []
retrieved = []
completed = False
failed = None
for event in Reader().agent_search_stream(
    "What compression ratio does KV-cache eviction report on LongBench?",
    effort="default",
):
    kind = event.get("event")
    if kind == "answer_delta":
        chunks.append(event.get("text", ""))
    elif kind == "answer":
        # Used when stream_answer=False; preserve the backend's supplied value.
        value = event.get("text", event.get("answer", ""))
        if isinstance(value, str):
            chunks.append(value)
    elif kind == "sources":
        retrieved = agent_search_sources(event)
    elif kind == "done":
        completed = event.get("answer_truncated") is False
    elif kind == "error":
        failed = {"stage": event.get("stage"), "message": event.get("message")}

answer = "".join(chunks)
if failed or not completed:
    raise RuntimeError({"partial_answer": answer, "error": failed,
                        "retrieved": retrieved})
```

`answer_delta` contains final-answer text only; verbose process events such as
`thinking`, `tool_call`, and `tool_result` are separate. The bundled
`../scripts/stream_agent_answer.py` equivalent should be preferred when a
terminal-safe stream adapter is needed. It exits with a distinct nonzero status
for truncation so an outer workflow cannot mistake it for success.

Do not auto-retry a timed-out or rate-limited agentic call. The SDK intentionally
makes no retry request because each run is quota-billed. Narrow the query,
reduce effort, or apply caller-owned backoff according to the account's policy.

## 3. Progressive arXiv reading: search -> brief -> head -> section

Start with a bounded semantic search and filters. `size` maps to upstream
`top_k`; an explicit `top_k` overrides `size`. Keep each page small enough to
screen before making more calls.

```python
from deepxiv_sdk import Reader

reader = Reader()
search = reader.search(
    "retrieval augmented generation evaluation",
    size=20,
    offset=0,
    source="arxiv",
    categories=["cs.CL", "cs.IR"],
    venue=["NeurIPS", "ICLR"],
    venue_year=2025,
    date_search_type="after",
    date_str="2024-01-01",
    use_fine_rerank=False,
)

candidates = search.get("result", [])
for item in candidates:
    paper_id = item.get("arxiv_id")
    if not paper_id:
        continue
    brief = reader.brief(paper_id)
    print(paper_id, brief.get("title"), brief.get("tldr"))
```

Select only candidates relevant to the user's task. For each selected ID:

```python
paper_id = "2409.05591"
head = reader.head(paper_id)
sections = head.get("sections", [])
if isinstance(sections, dict):
    section_items = ((name, info) for name, info in sections.items())
else:
    section_items = (
        (item.get("name"), item) for item in sections
        if isinstance(item, dict)
    )
for name, info in section_items:
    print(name, info.get("token_count"), info.get("tldr"))

# `section()` accepts case-insensitive and partial names.
method_text = reader.section(paper_id, "Method")
result_text = reader.section(paper_id, "Results")
```

If structure is not yet known, call `head` before `section`. If only a quick scan
is needed, `preview` returns a bounded dictionary; check `is_truncated`. Use
`raw`/`json` only for a whole-paper task. A paper's `head` sections are current
service data and may be a list; do not use the old example's `.items()` pattern.

### Pagination without loading full papers

```python
all_items = []
page_size = 100
for offset in range(0, 501, page_size):
    page = reader.search("long-context agents", size=page_size, offset=offset)
    items = page.get("result", [])
    all_items.extend(items)
    if not items or len(all_items) >= page.get("total_count", len(all_items)):
        break
```

The public bounds are `size/top_k` 1–100 and `offset` 0–10,000. Stop on an empty
page and impose the task's own maximum; `total_count` is service metadata, not a
guarantee that every later page remains unchanged. Brief and head only selected
IDs; never call `raw` in the pagination loop.

## 4. Baseline table recipe

Use this route for a comparison-ready survey:

1. Search with the exact topic plus category, venue, date, author, organization,
   and citation filters that are genuinely required.
2. Read `result` items and deduplicate by the source-specific ID.
3. Call `brief` for all plausible candidates and record title, TLDR, date,
   keywords, citations, and GitHub URL when returned.
4. Call `head` only for retained papers and identify `Experiments`, `Evaluation`,
   `Results`, or equivalent sections.
5. Call one or two selected sections and extract datasets, metrics, scores,
   settings, and limitations. If a value is not explicit, record
   `Not clearly stated` rather than inferring it.
6. Label each table row as brief-only, head-checked, or section-checked. Keep
   code/open-source status `Unknown` when no verified URL is present.

A useful row schema is:

```python
row = {
    "title": brief.get("title"),
    "id": paper_id,
    "paper_url": brief.get("src_url"),
    "github_url": brief.get("github_url"),
    "evidence_level": "section-checked",
    "datasets": [],
    "metrics_and_scores": "Not clearly stated",
    "notes": "",
}
```

Do not claim that papers are directly comparable when datasets, models, or
metrics differ. The existing baseline-table workflow's bounded search/brief/head/
experiment-section order is the intended pattern.

## 5. Trending digest and social signal recipe

For a recent digest, call `trending(days=7, limit=10)` first. The normal return
has `papers`, `total`, `days`, and `generated_at`; each paper commonly has an
`arxiv_id`, `rank`, and `stats`. Brief each candidate, choose one to three for
`head`, then read only a high-value section. State which conclusions are based
only on brief versus section text.

```python
trend = reader.trending(days=7, limit=10)
for item in trend.get("papers", []):
    paper_id = item.get("arxiv_id")
    if paper_id:
        brief = reader.brief(paper_id)
        print(item.get("rank"), paper_id, brief.get("title"), brief.get("tldr"))
```

`social_impact(arxiv_id)` is a separate, token-required lookup. It may return a
metrics dictionary or `None` when no signal exists; do not turn missing social
data into a zero. Treat views, tweets, likes, and replies as attention signals,
not evidence that the paper is correct or important.

## 6. PMC and biomedical preprints

Use `pmc_head(pmc_id)` for metadata and `pmc_full(pmc_id)`/`pmc_json(pmc_id)` for
structured full data. Keep `PMC...` IDs distinct from arXiv IDs.

For bioRxiv/medRxiv, first call `biomed_search(query, source="biorxiv" or
"medrxiv")`. Then pass a returned DOI-like ID to `biomed_data`:

```python
hits = reader.biomed_search("host response to respiratory virus",
                            source="medrxiv", top_k=10)
for hit in hits.get("result", []):
    source_id = hit.get("medrxiv_id")
    if source_id:
        metadata = reader.biomed_data(source_id, source="medrxiv",
                                       data_type="metadata")
```

`biomed_data` also supports `data_type="section"` with `section_names=[...]`
and `data_type="roc"` with `roc_num=...`; use these only when the task needs
those fields. The retrieve call is metadata/ranking, not full content.
