# Sources, citations, and evidence strength

A Reader result contains several different notions of “source”. Keep them
separate in notes and output.

## Hosted arXiv answers

For `Reader.agent_search(..., source="arxiv")`:

- `result["answer"]` is the generated answer string.
- `result["sources"]` is the retrieval set. It can contain papers that were
  retrieved but not cited in the answer.
- Each paper normally has `arxiv_id`, `title`, and `url`. Preserve the ID exactly;
  it is the stable citation handle exposed by this API.
- A conservative cited set is the subset whose `arxiv_id` occurs in the answer,
  but treat that as a practical extraction rule rather than proof that every
  citation mention was parsed perfectly.
- A citation such as `[arXiv:2409.05591]` can be checked against the returned
  source record and its URL. Never invent an ID when the service did not return
  it.

For streaming, the `sources` event uses `papers`, not `sources`. Use
`agent_search_sources(event)` so blocking and streaming code share one path:

```python
from deepxiv_sdk import agent_search_sources

retrieved = []
for event in reader.agent_search_stream(question):
    if event.get("event") == "sources":
        retrieved = agent_search_sources(event)
# `retrieved` is still the retrieval set, not automatically the cited set.
```

Do not call the answer complete merely because a `done` event arrived. Require
`done.get("answer_truncated") is False`. If an `error` event appears, retain any
partial text only as an explicitly partial/error result.

## Hosted web answers

For `source="web"`, normalized source records normally have:

```python
{
    "url": "https://…",
    "title": "…",
    "read": True,  # or False
}
```

The backend reads cached page bodies; it does not fetch a live page during the
agentic run. Therefore:

- `read: true` means the service read the cached page body. It is the stronger
  evidence class for a claim grounded in page content.
- `read: false` means the page contributed only a retrieved search snippet. It is
  weaker and may omit context, qualifiers, date, or the actual detail.
- A page can be in the retrieval set without its URL appearing in the answer.
  Match URL mentions to report cited pages; retain uncited pages separately.
- Never describe a snippet-only page as “read” or imply that the service verified
  its live current contents. Qualify claims based on it.

The same stream event semantics apply: `pages` appears in a web `sources` event,
while a blocking response uses `sources`; `agent_search_sources` normalizes both.

## Truncation and partial evidence

Track these states independently:

| State | Meaning | Safe report wording |
| --- | --- | --- |
| `done.answer_truncated == False` | The backend says the answer reached a normal completion | “Answer completed”; still preserve citations |
| `done.answer_truncated == True` | The answer hit the configured cap | “Incomplete/truncated answer”; ask for a higher cap or narrower question |
| `error` event | The run failed at a reported stage; partial deltas may exist | “Partial answer; run failed at `<stage>`” |
| no `done` event | Completion was not observed | “Unconfirmed/incomplete”; do not publish as final |

For blocking responses, use `stats.answer_truncated` with the same rule. A
truncated answer may have a valid-looking citation near its beginning, but it is
still unsafe to summarize as a complete answer. Increase `max_answer_tokens` only
within the inclusive 256–16,384 range, or narrow the question and request the
missing point directly.

## Evidence ledger pattern

When synthesizing a result, create a small ledger instead of flattening all
sources into one bibliography:

```python
ledger = {
    "answer_complete": False,
    "answer_text": "…",
    "cited_arxiv": [
        {"arxiv_id": "…", "title": "…", "url": "…", "basis": "ID in answer"}
    ],
    "retrieved_uncited_arxiv": [],
    "cited_web_read": [],
    "cited_web_snippet_only": [],
    "partial_or_failed": False,
}
```

Populate `cited_web_read` and `cited_web_snippet_only` by matching URLs in the
answer and then checking `page.get("read")`. The absence of `read` is not a
license to assume full reading; label unknown fields as unknown. Keep the raw
answer and the `stats`/`done` metadata alongside the ledger when auditability
matters.

## Direct paper-reading evidence

The progressive Reader methods have different evidentiary scope:

- `brief` is a screening summary. It can contain TLDR, keywords, citations,
  publication date, PDF URL, and GitHub URL when available; it is not a proof that
  an experiment or number appears in the paper.
- `head` supplies paper metadata and section structure, including per-section
  summaries/token counts when the service returns them. It tells you where to
  read; it does not replace the section body.
- `section` is the preferred evidence for a focused method, evaluation, result,
  or limitation claim. Record the canonical section name chosen by the SDK's
  case-insensitive/partial matcher.
- `preview` is a bounded beginning-of-paper scan and may be truncated. Check its
  `is_truncated` field and do not treat it as complete paper evidence.
- `raw` and `json` are complete-content routes and can be very large; use them
  only when the task explicitly requires whole-paper access.

For a baseline table, leave a metric as “Not clearly stated” if the inspected
section does not state it. For a trending digest, distinguish paper conclusions
based only on `brief` from those checked with `head` or a section. Do not infer
open-source status from a missing GitHub field.

## Identifier discipline across sources

- arXiv paper methods take an `arxiv_id`, such as `2409.05591`.
- PMC methods take a `pmc_id`, such as `PMC544940`.
- `biomed_data` takes a bioRxiv/medRxiv DOI-like `source_id`, such as
  `10.1101/2021.02.26.433129`; the `source` argument selects the collection.
- Trending and social impact are arXiv-oriented and return/use arXiv IDs.

Keep the namespace in every synthesized row. A DOI-like biomedical ID must not be
rendered as an arXiv citation, and an arXiv ID must not be sent to `biomed_data`.
