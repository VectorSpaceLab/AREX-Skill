# Python Extraction Workflows

These recipes use no live network access. They assume an HTML string, bytes payload, response body, or LXML tree is already available.

## 1. Pick the right API

Use this decision order:

1. Need a serialized output string? Use `extract()`.
2. Need Python attributes, raw LXML body/comments trees, or post-processing before serialization? Use `bare_extraction()`.
3. Need serialized extracted content plus metadata attributes on the same object? Use `extract_with_metadata()`.
4. Need only metadata? Use `extract_metadata()`.
5. Need a fallback that grabs as much visible text as possible? Use `html2txt()`.
6. Need a fast simple baseline tuple for diagnostics? Use `baseline()`.
7. Need to normalize bytes/response/LXML inputs first? Use `load_html()`.

## 2. Basic in-memory article extraction

```python
from trafilatura import extract

html = """
<html>
  <head><title>Example page</title></head>
  <body>
    <nav>Home | Archive</nav>
    <article>
      <h1>Example page</h1>
      <p>This is the first paragraph of the article.</p>
      <p>This is the second paragraph with enough content to extract.</p>
    </article>
    <footer>Copyright</footer>
  </body>
</html>
"""

text = extract(html, include_comments=False)
if text is None:
    raise RuntimeError("Trafilatura discarded the input")
print(text)
```

Prefer `include_comments=False` for article-only tasks; leave it at the default when comments are a desired part of the extracted document.

## 3. JSON output with metadata and links

```python
import json
from trafilatura import extract

html = """
<html>
  <head>
    <title>Research note</title>
    <meta name="author" content="Ada Example">
    <meta property="article:published_time" content="2024-05-02">
    <meta name="description" content="A short example article.">
  </head>
  <body>
    <article>
      <h1>Research note</h1>
      <p>See <a href="/paper">the paper</a> for details.</p>
    </article>
  </body>
</html>
"""

payload = extract(
    html,
    url="https://example.org/news/research-note",
    output_format="json",
    with_metadata=True,
    include_comments=False,
    include_links=True,
)
if payload is None:
    raise RuntimeError("No extractable article")
record = json.loads(payload)
print(record["title"], record["author"], record["date"], record["source"])
print(record["text"])
```

Notes:

- JSON output is the easiest format to assert in memory.
- `include_formatting=True` has no effect on JSON.
- Metadata field names differ from `Document` attributes for some fields: URL is `source`, sitename is `source-hostname`, and description is `excerpt`.

## 4. Markdown with YAML-style metadata

```python
from trafilatura import extract

markdown = extract(
    html,
    url="https://example.org/news/research-note",
    output_format="markdown",
    with_metadata=True,
    include_comments=False,
    include_links=True,
)
if markdown is None:
    raise RuntimeError("No Markdown produced")
print(markdown)
```

Expect output shaped like:

```markdown
---
title: Research note
author: Ada Example
url: https://example.org/news/research-note
date: 2024-05-02
---
# Research note

See [the paper](https://example.org/paper) for details.
```

Actual heading depth and formatting depend on the source tree and Trafilatura's conversion. Values that need escaping are double-quoted in the metadata header.

## 5. Work with `Document` objects

Use `bare_extraction()` when downstream code needs both text and parsed structure.

```python
from lxml import etree
from trafilatura import bare_extraction

doc = bare_extraction(
    html,
    url="https://example.org/news/research-note",
    with_metadata=True,
    include_comments=False,
)
if doc is None:
    raise RuntimeError("No document")

print(doc.title, doc.author, doc.date)
print(doc.text)                # text for output_format="python"
print(doc.comments or "")
print(etree.tostring(doc.body, encoding="unicode"))
```

For a dictionary:

```python
record = doc.as_dict()
```

Do not use `as_dict=True` unless you are maintaining older code; it is deprecated.

## 6. `extract_with_metadata()` for text plus attributes

```python
from trafilatura import extract_with_metadata

doc = extract_with_metadata(
    html,
    url="https://example.org/news/research-note",
    output_format="txt",
    include_formatting=True,
    include_comments=False,
)
if doc is None:
    raise RuntimeError("No extracted document")
print(doc.title, doc.date)
print(doc.text)
```

Use this when the output string format matters but you still need metadata attributes. For Python/LXML bodies, use `bare_extraction()` instead.

## 7. Metadata-only extraction

```python
from trafilatura import extract_metadata

meta = extract_metadata(html, default_url="https://example.org/news/research-note")
print(meta.title, meta.author, meta.date, meta.url, meta.hostname)
```

Date parsing is delegated to `htmldate`. Tune it with a date config:

```python
meta = extract_metadata(
    html,
    default_url="https://example.org/news/research-note",
    date_config={
        "original_date": True,
        "extensive_search": True,
        "max_date": "2024-12-31",
    },
)
```

For full extraction, pass the same idea as `date_extraction_params=`.

## 8. Parse once, extract many times

```python
from trafilatura import extract, load_html

tree = load_html(html_bytes)
if tree is None:
    raise ValueError("Input is not usable HTML")

text = extract(tree, include_comments=False)
json_payload = extract(tree, output_format="json", with_metadata=True)
```

When passing a caller-owned LXML tree to Trafilatura APIs, assume extraction may copy or transform internals as part of processing. Keep the original input if it matters to downstream code.

## 9. Response-like objects

If another workflow already fetched content and has a response-like object, pass its body or `.data` content to this sub-skill's APIs. Preserve final URL separately when available.

```python
# response comes from another workflow; this recipe does not fetch it.
text = extract(response.data, url=response.url, include_comments=False)
```

Passing `url=` is still valuable because redirects, URL metadata, date extraction, and relative link conversion can depend on it.

## 10. Custom `Extractor` for repeated calls

```python
from trafilatura import extract
from trafilatura.settings import Extractor

options = Extractor(
    output_format="json",
    fast=True,
    comments=False,
    tables=False,
    links=True,
    url="https://example.org/base/",
    with_metadata=True,
)

records = []
for html_doc in html_documents:
    out = extract(html_doc, options=options)
    if out is not None:
        records.append(out)
```

Use separate `Extractor` instances if different calls need different URLs or mutable settings. A shared options object carries source URL, focus, and size thresholds.

## 11. Prune known boilerplate before extraction

```python
from trafilatura import extract

text = extract(
    html,
    prune_xpath=[
        "//div[contains(@class, 'newsletter')]",
        "//aside",
        "//section[contains(@class, 'related')]",
    ],
    include_comments=False,
)
```

Use `prune_xpath` when you know the HTML structure and can safely remove site-specific blocks. If a broad XPath removes article content, extraction can return `None` or become too short.

## 12. Tune output size thresholds with config

```python
from copy import deepcopy
from trafilatura import extract
from trafilatura.settings import DEFAULT_CONFIG

config = deepcopy(DEFAULT_CONFIG)
config["DEFAULT"]["MIN_OUTPUT_SIZE"] = "20"
config["DEFAULT"]["MIN_EXTRACTED_SIZE"] = "100"

text = extract(html, config=config)
```

For large output trees, set `MAX_TREE_SIZE` through config rather than the deprecated direct `max_tree_size=` argument:

```python
config = deepcopy(DEFAULT_CONFIG)
config["DEFAULT"]["MAX_TREE_SIZE"] = "5000"
text = extract(html, config=config)
```

## 13. Failure-aware fallback ladder for `None` or too-short text

When `extract()` returns `None`, do not immediately assume the page is empty. Try a bounded ladder:

```python
from trafilatura import baseline, extract, html2txt

text = extract(html, include_comments=False)

if text is None:
    # Try more recall before giving up.
    text = extract(html, include_comments=False, favor_recall=True)

if text is None:
    # Fast mode can help if slow fallbacks are choking on strange markup, but can also reduce recall.
    text = extract(html, include_comments=False, fast=True, favor_recall=True)

if text is None:
    # Site-specific cleanup.
    text = extract(html, prune_xpath=["//nav", "//footer", "//aside"], favor_recall=True)

if text is None:
    # Article-focused baseline tuple.
    _, base_text, base_len = baseline(html)
    text = base_text if base_len else None

if text is None:
    # Last resort: all visible text.
    text = html2txt(html) or None
```

Decision tips:

- Use `favor_recall=True` when content is missing or too short.
- Use `favor_precision=True` when noise leaks into output.
- Use `fast=True` for clean pages or large batches, not as the first fix for missing content.
- Use `html2txt()` only when a noisy all-text fallback is acceptable.
- If `only_with_metadata=True` caused `None`, retry without it or provide `url=` and date parameters.

## 14. Validate in memory

The bundled smoke script provides a quick no-network check:

```bash
python skills/disco/trafilatura/sub-skills/python-extraction/scripts/extraction_smoke.py
```

For your own assertions, prefer JSON or `Document` output:

```python
import json
from trafilatura import extract

payload = extract(html, output_format="json", with_metadata=True, include_comments=False)
assert payload is not None
record = json.loads(payload)
assert "expected phrase" in record["text"]
assert record["date"] == "2024-05-02"
```
