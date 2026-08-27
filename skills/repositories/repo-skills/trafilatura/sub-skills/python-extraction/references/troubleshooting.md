# Python Extraction Troubleshooting

Use this guide when Trafilatura's Python extraction APIs return `None`, produce unexpectedly short text, miss metadata, or serialize output in a surprising way.

## Quick symptom table

| Symptom | Likely cause | First checks | Fixes |
| --- | --- | --- | --- |
| `extract()` returns `None` | Invalid input, too short output, metadata/language/blacklist rejection, dedup rejection, or config limit. | Try `load_html()`, `baseline()`, and `html2txt()` on the same input. Check `only_with_metadata`, `target_language`, blacklists, and size config. | Retry with `favor_recall=True`, provide `url=`, lower size thresholds in `config`, remove strict filters, or use fallback APIs. |
| `bare_extraction()` returns `None` | Same discard paths as `extract()`. | Verify `doc is not None` before accessing attributes. | Same as above; use `with_metadata=False` if metadata gates are too strict. |
| Empty string from `html2txt()` | Not usable HTML text or no body/content. | Call `load_html()` and inspect whether a tree exists. | Wrap fragments in a full HTML document or pass an LXML element containing content. |
| Text misses article sections | Precision/fallback rules excluded uncertain content. | Compare default vs `favor_recall=True`, `baseline()`, and `html2txt()`. | Use recall, remove overly broad `prune_xpath`, include tables/comments if they hold content. |
| Text contains boilerplate | Page layout/noise survived extraction. | Check nav/footer/aside/classes in source HTML. | Use `favor_precision=True`, `include_comments=False`, `include_tables=False`, or targeted `prune_xpath`. |
| Metadata missing | HTML lacks reliable metadata or URL/date context. | Run `extract_metadata()` and inspect `title`, `author`, `date`, `url`. | Pass `url=`, tune `date_extraction_params`, avoid `only_with_metadata=True` unless required. |
| Language filter rejects output | `target_language` mismatch or weak optional detector state. | Check `<html lang>` and meta content-language. Know whether optional language detector is installed. | Remove `target_language`, install optional language extras, or validate language outside Trafilatura. |
| Markdown/XML links missing | Output format or flags do not preserve links. | Confirm `include_links=True` and `url=` for relative links. | Use Markdown/XML/HTML, not JSON, when link structure must be visible. |
| Direct `max_tree_size=` raises | Deprecated direct argument in 2.2.0. | Look for a `ValueError` mentioning `max_tree_size`. | Set `MAX_TREE_SIZE` in a copied config or settings file instead. |

## `None` output checklist

1. Confirm input type:

```python
from trafilatura import load_html

tree = load_html(html)
if tree is None:
    print("Not a usable full HTML document")
```

2. Check fallbacks:

```python
from trafilatura import baseline, html2txt

_, base_text, base_len = baseline(html)
all_text = html2txt(html)
print(base_len, all_text[:200])
```

3. Remove strict gates one at a time:

- Temporarily set `only_with_metadata=False`.
- Temporarily remove `target_language`.
- Temporarily remove `url_blacklist`, `author_blacklist`, and `deduplicate=True`.
- Temporarily remove `prune_xpath`.
- Retry without a custom config or settings file.

4. Increase recall:

```python
text = extract(html, favor_recall=True, include_comments=False)
```

5. If text is too noisy, switch direction:

```python
text = extract(html, favor_precision=True, include_comments=False, include_tables=False)
```

## Fragments and malformed HTML

`load_html()` is conservative about tiny non-document fragments. This can fail:

```python
extract("<p>One sentence.</p>")
```

Prefer:

```python
fragment = "<p>One sentence with enough useful content.</p>"
html = f"<html><body><article>{fragment}</article></body></html>"
text = extract(html)
```

For badly malformed but document-like HTML, Trafilatura attempts repairs before parsing. If the parser still rejects it, use an HTML parser upstream to normalize the tree, then pass an `lxml.html.HtmlElement`.

## Too-short inputs and size thresholds

Default settings are article-oriented. Very short content can be discarded depending on thresholds and extraction path. For controlled tests or short snippets, lower thresholds with a copied config:

```python
from copy import deepcopy
from trafilatura import extract
from trafilatura.settings import DEFAULT_CONFIG

config = deepcopy(DEFAULT_CONFIG)
config["DEFAULT"]["MIN_OUTPUT_SIZE"] = "1"
config["DEFAULT"]["MIN_EXTRACTED_SIZE"] = "1"
text = extract(html, config=config)
```

Do not edit global package settings for a one-off task unless the whole process should inherit the change.

## Optional language detection limits

`target_language="de"` or similar may reject output. Reliable body-language filtering depends on optional language detection components included by extras such as `trafilatura[all]`. Without them, filtering may rely mainly on HTML language metadata when present.

Guidance:

- Use `target_language` only when rejecting mismatches is acceptable.
- If no optional detector is installed, do not treat a pass/fail as a full text-language classifier.
- For critical language gates, validate the output with a dedicated language identification step after extraction.

## Metadata and date surprises

Common causes:

- No `url=` was passed, so hostname, URL, URL-derived date hints, and relative link handling are weaker.
- HTML metadata is absent or too generic.
- Date extraction defaults reject dates after the configured `max_date`.
- `only_with_metadata=True` requires title, date, and URL.
- Author fields can be dropped if `author_blacklist` matches.

Use metadata-only diagnostics:

```python
from trafilatura import extract_metadata

meta = extract_metadata(html, default_url="https://example.org/article")
print(meta.as_dict())
```

Tune dates:

```python
text = extract(
    html,
    url="https://example.org/article",
    with_metadata=True,
    date_extraction_params={
        "original_date": True,
        "extensive_search": True,
        "max_date": "2024-12-31",
    },
)
```

If `only_with_metadata=True` returns `None`, first prove that `extract_metadata()` can find all required fields.

## Comments, tables, links, images, and formatting

- Comments and tables are included by default. Disable them when they introduce noise:

```python
text = extract(html, include_comments=False, include_tables=False)
```

- Links need both `include_links=True` and an output format that can represent links. Pass `url=` to resolve relative links.
- Images are experimental and only visible in formats that serialize them, such as Markdown or XML.
- Markdown implies formatting by default. Use `include_formatting=False` to flatten text.
- JSON output intentionally ignores formatting and emits extracted text/comments, not rich inline markup.

## Markdown quirks

- `with_metadata=True` adds a YAML-style header before the content.
- Metadata scalar values may be double-quoted when needed for YAML safety.
- `output_format="txt"` plus `include_formatting=True` can resemble Markdown because formatting is serialized into plain text markers.
- Headings, emphasis, superscript/subscript, code, and links depend on what Trafilatura preserved from the source tree.

When tests must assert stable output, prefer substring assertions for prose and JSON field assertions for metadata.

## XML and XML-TEI quirks

- XML output uses extracted structure, not the original source DOM.
- Metadata is represented as attributes when available.
- `include_links=True` serializes links as XML references in supported XML paths.
- `include_images=True` serializes image-like records as graphics in XML paths.
- `output_format="xmltei"` enables metadata internally and can include TEI-specific structure.
- `tei_validation=True` only applies to `xmltei`. Treat it as a diagnostic flag; corpus-level TEI validation belongs to the quality/corpus workflow.

## `Extractor` misuse

Problem patterns:

- Reusing one `Extractor(url=...)` for documents from different URLs. Create a new options object per URL or update the URL intentionally.
- Passing both `precision=True` and `recall=True`; recall wins.
- Expecting `formatting=True` to affect JSON; JSON ignores it.
- Expecting `output_format="python"` to work with `extract()` or `extract_with_metadata()`; use `bare_extraction()`.

## Safe fallback strategy

Use a bounded ladder and record which level produced the result:

1. `extract(html, include_comments=False)`.
2. `extract(..., favor_recall=True)` for missing content.
3. `extract(..., favor_precision=True)` for noisy content.
4. `extract(..., prune_xpath=[...])` when boilerplate selectors are known.
5. `baseline(html)` for article-ish fallback diagnostics.
6. `html2txt(html)` only when all visible text is acceptable.

Avoid silently replacing `None` with `html2txt()` in production if precision matters; label the fallback in downstream metadata or logs.
