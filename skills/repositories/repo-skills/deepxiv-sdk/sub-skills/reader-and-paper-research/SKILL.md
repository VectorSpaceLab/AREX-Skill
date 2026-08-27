---
name: reader-and-paper-research
description: "Use the DeepXiv Reader for hosted arXiv/web agentic research,
  progressive paper reading, semantic and biomedical search, PMC retrieval, and
  trending or social-impact evidence."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Reader and paper research

Use this route when the task needs the Python `deepxiv_sdk.Reader`: a cited hosted
answer, arXiv paper discovery and selective reading, PMC or bioRxiv/medRxiv data,
or trending/social-impact signals. The public API is described in
[references/api-reference.md](references/api-reference.md); reusable recipes are in
[references/workflows.md](references/workflows.md); source/citation interpretation is
in [references/source-and-citations.md](references/source-and-citations.md); and
recovery guidance is in [references/troubleshooting.md](references/troubleshooting.md).

## Route first

1. Import `Reader` and construct it with an optional user-provided token. Do not
   print, persist, or place a token in source files. Agentic endpoints require a
   registered account key; ordinary paper/search calls have a separate quota.
2. For a hosted answer, choose `source="arxiv"` for academic full-text evidence or
   `source="web"` for current/non-academic material. Write a specific question,
   choose `effort` deliberately, and inspect the completion's truncation flag.
3. For controlled literature work, use `search` and pagination, then load each
   candidate as `brief` -> `head` -> selected `section` (or `preview`). Avoid
   `raw`/`json` unless the task needs the complete paper.
4. Preserve source IDs and URLs, and distinguish the retrieval set from sources
   actually cited by the answer. For web results, `read: true` is stronger than
   snippet-only evidence.
5. Treat a streamed `error` event as a failed/incomplete run even though the SDK
   yields it instead of raising. Treat `answer_truncated: true` as incomplete.

The bundled [streaming adapter](scripts/stream_agent_answer.py) is a safe
adapter that prints the answer while sending source/truncation diagnostics to
stderr and exits non-zero for errors or truncation. The [Reader probe](scripts/reader_probe.py)
performs import, constructor, and validation checks without network access. Both
can be invoked from any working directory by using their installed/runtime path.

## Boundaries and sibling routes

- Shell command names, flags, stdout/stderr behavior, and local token configuration
  belong to [CLI and operations](../cli-and-operations/SKILL.md), not this route.
- The optional local OpenAI-compatible LangGraph `Agent`, its graph/tools, and
  local model budgets belong to [optional local agent](../optional-local-agent/SKILL.md).
- Package installation and cross-package provenance belong to the
  [DeepXiv SDK root route](../../SKILL.md).

Do not substitute historical example snippets for the current public API:
`preview()` has no `max_tokens` argument and search returns `result`, not
`results`. Use the bundled references and current public signatures.

## Minimal selection rules

- Use blocking `agent_search()` when the caller can wait for one dictionary.
- Use `agent_search_stream()` for interactive output or long answers; reassemble
  `answer_delta` text and gate publication on the final `done` event.
- Set `effort="default"` for a narrow, latency-sensitive question; use `high`
  for comparisons and `xhigh` for broad synthesis only after improving the query.
  Increasing effort adds gathering rounds but cannot repair poor first-round recall.
- Use `search(..., use_fine_rerank=True)` only when ordering quality justifies the
  extra upstream work; the SDK default is `False`.
- Put year, venue, category, author, organization, or citation constraints in
  `search` filters. Filters combine, so loosen one when a result set is empty.
- For an answer about one paper, prefer `brief`, `head`, and one or two sections;
  do not load all papers with `raw`.

For exact argument validation, response fields, exception mapping, retries, and
backend-specific options, read the linked references before making a live call.
