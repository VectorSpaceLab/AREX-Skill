---
name: python-extraction
description: "Use Trafilatura's Python APIs to extract text, metadata, comments,
  tables, and structured TXT/Markdown/JSON/HTML/XML/XML-TEI from in-memory HTML
  inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Python Extraction

Use this sub-skill when a task needs Trafilatura's Python API to turn an already available HTML payload, response body, or parsed LXML tree into extracted article text, metadata, comments, tables, or structured output.

## Route here

- In-memory extraction from `str`, `bytes`, response-like objects with `.data`, or `lxml.html.HtmlElement` inputs.
- Choosing between `extract()`, `bare_extraction()`, `extract_with_metadata()`, `extract_metadata()`, `html2txt()`, `baseline()`, and `load_html()`.
- Selecting `output_format` among `txt`, `markdown`, `json`, `html`, `csv`, `xml`, and `xmltei`.
- Using metadata/comment/table/link/image/formatting flags, precision/recall/fast modes, `Extractor` settings objects, `prune_xpath`, date parameters, language filtering, and config-driven size limits.
- Diagnosing `None` output, too-short results, malformed HTML, metadata/date surprises, and Markdown/XML conversion quirks.

## Route elsewhere

- CLI flags, shell pipelines, filesystem output, batch command construction, or stdin/stdout behavior: `cli-batch-processing`.
- Live downloading, feed/sitemap discovery, URL queues, crawl loops, or response fetching: `discovery-downloads`.
- Corpus-level deduplication strategy, TEI validation depth, benchmark evaluation, or quality scoring: `corpus-quality`.

## Start points

1. Read [references/api-reference.md](references/api-reference.md) for function signatures, return shapes, option semantics, and output-format tradeoffs.
2. Use [references/workflows.md](references/workflows.md) for copy-paste Python recipes and failure-aware extraction decisions.
3. Use [references/troubleshooting.md](references/troubleshooting.md) when extraction returns `None`, metadata is missing, language filtering behaves unexpectedly, or output formatting looks wrong.
4. Run [scripts/extraction_smoke.py](scripts/extraction_smoke.py) in an environment with `trafilatura` installed to verify the basic no-network API surface.

## Minimal pattern

```python
from trafilatura import extract

html = """<html><body><article><h1>Title</h1><p>Main article text.</p></article></body></html>"""
text = extract(html, include_comments=False)
if text is None:
    # Retry with recall or a fallback API; see references/workflows.md.
    ...
```

## Safety and scope notes

- This sub-skill assumes HTML is already available. Do not initiate live network access from these recipes unless another sub-skill has explicitly selected and prepared that workflow.
- Public runtime guidance here is self-contained for Trafilatura 2.2.0 and does not require reopening the source repository.
- Some optional behavior, especially robust `target_language` body-language detection and speedups, depends on optional extras such as `trafilatura[all]`; handle absence as a runtime capability limit, not as an extraction bug.
