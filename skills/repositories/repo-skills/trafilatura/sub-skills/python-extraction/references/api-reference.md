# Trafilatura Python Extraction API Reference

This reference targets `trafilatura==2.2.0` and the in-memory extraction workflows owned by the `python-extraction` sub-skill.

## Imports

```python
from trafilatura import (
    extract,
    bare_extraction,
    extract_with_metadata,
    extract_metadata,
    html2txt,
    baseline,
    load_html,
)
from trafilatura.settings import DEFAULT_CONFIG, Extractor, use_config
```

Accepted content inputs for the core extraction helpers are:

- `str` containing a full HTML document.
- `bytes` containing a full HTML document.
- Trafilatura/urllib3-style response objects, or any object with a `.data` payload, for `load_html()` and extraction functions.
- `lxml.html.HtmlElement` trees.

`load_html()` expects a document-like HTML input. A single tiny fragment such as `<p>x</p>` can be rejected as not-quite-HTML; wrap fragments in a document or larger container before extraction.

## Core functions and return shapes

| Function | Use when | Return shape | Important notes |
| --- | --- | --- | --- |
| `extract(filecontent, ..., output_format="txt", ...)` | You want the simplest API and a serialized output string. | `str` or `None`. | Does text extraction and output conversion. `output_format="python"` is not valid here; use `bare_extraction()` for Python objects. |
| `bare_extraction(filecontent, ..., output_format="python", ...)` | You need a `Document` object with `.text`, `.comments`, `.body`, `.commentsbody`, and metadata attributes. | `Document`, `dict`, or `None`. | Default `output_format="python"` keeps Python/LXML structures. `as_dict=True` is deprecated; prefer `doc.as_dict()` after a non-`None` return. |
| `extract_with_metadata(filecontent, ..., output_format="txt", ...)` | You want serialized text in `doc.text` plus metadata attributes on the same object. | `Document` or `None`. | Equivalent to extraction with metadata enabled. Raises if `output_format="python"`; use `bare_extraction(..., with_metadata=True)` instead. |
| `extract_metadata(filecontent, default_url=None, date_config=None, extensive=True, author_blacklist=None)` | You only need metadata such as title, author, URL, hostname, date, tags, categories, license. | `Document` object. | Does not perform main text extraction. Invalid HTML returns an empty `Document`, not `None`. |
| `html2txt(content, clean=True)` | You need a last-resort all-visible-text fallback. | `str`; empty string when no text. | Maximizes recall and ignores article-focused precision. Removes undesirable elements when `clean=True`. |
| `baseline(filecontent)` | You need a fast fallback targeting embedded JSON, article tags, paragraphs, or body text. | `(body_element, text, length)`. | Returns an LXML `<body>` element, extracted text, and text length. Invalid/empty input returns `(Element("body"), "", 0)`. |
| `load_html(htmlobject)` | You need to normalize bytes/strings/response/tree inputs into an LXML tree. | `HtmlElement` or `None`. | Accepts response-like `.data`; raises `TypeError` for incompatible types; returns `None` for empty or invalid HTML-like payloads. |

## Main extraction signatures

```python
extract(
    filecontent,
    url=None,
    record_id=None,
    fast=False,
    no_fallback=False,
    favor_precision=False,
    favor_recall=False,
    include_comments=True,
    output_format="txt",
    tei_validation=False,
    target_language=None,
    include_tables=True,
    include_images=False,
    include_formatting=None,
    include_links=False,
    deduplicate=False,
    date_extraction_params=None,
    with_metadata=False,
    only_with_metadata=False,
    max_tree_size=None,
    url_blacklist=None,
    author_blacklist=None,
    settingsfile=None,
    prune_xpath=None,
    config=DEFAULT_CONFIG,
    options=None,
) -> str | None
```

```python
bare_extraction(
    filecontent,
    url=None,
    fast=False,
    no_fallback=False,
    favor_precision=False,
    favor_recall=False,
    include_comments=True,
    output_format="python",
    target_language=None,
    include_tables=True,
    include_images=False,
    include_formatting=None,
    include_links=False,
    deduplicate=False,
    date_extraction_params=None,
    with_metadata=False,
    only_with_metadata=False,
    max_tree_size=None,
    url_blacklist=None,
    author_blacklist=None,
    as_dict=False,
    prune_xpath=None,
    config=DEFAULT_CONFIG,
    options=None,
) -> Document | dict | None
```

```python
extract_with_metadata(
    filecontent,
    url=None,
    record_id=None,
    fast=False,
    favor_precision=False,
    favor_recall=False,
    include_comments=True,
    output_format="txt",
    tei_validation=False,
    target_language=None,
    include_tables=True,
    include_images=False,
    include_formatting=None,
    include_links=False,
    deduplicate=False,
    date_extraction_params=None,
    url_blacklist=None,
    author_blacklist=None,
    settingsfile=None,
    prune_xpath=None,
    config=DEFAULT_CONFIG,
    options=None,
) -> Document | None
```

## `Document` attributes

`bare_extraction()`, `extract_with_metadata()`, and `extract_metadata()` use Trafilatura's `Document` class. Relevant attributes include:

- Metadata: `title`, `author`, `url`, `hostname`, `description`, `sitename`, `date`, `categories`, `tags`, `fingerprint`, `id`, `license`, `language`, `image`, `pagetype`, `filedate`.
- Content: `body` (LXML element), `commentsbody` (LXML element), `text` (serialized output for `extract_with_metadata()` or Python text for `bare_extraction()`), `comments`, `raw_text`.
- Conversion: `doc.as_dict()` returns a plain dictionary containing all slots.

Always guard for `None` before dereferencing:

```python
doc = bare_extraction(html, with_metadata=True)
if doc is None:
    raise ValueError("Trafilatura discarded the input")
print(doc.title, doc.date, doc.text)
```

## Output format matrix

| `output_format` | Supported by | Best for | Metadata behavior | Structural quirks |
| --- | --- | --- | --- | --- |
| `txt` | `extract`, `extract_with_metadata`, `bare_extraction` | Plain article text. | With `with_metadata=True`, text output gets a YAML-style header. | `include_formatting=True` can emit Markdown-like markers for emphasis/code/heads. Links/images may be invisible unless formatting/output supports them. |
| `markdown` | All extraction helpers | Human-readable text with headings, emphasis, links, and images. | With `with_metadata=True`, output starts with a YAML-style metadata header. | Markdown implies formatting by default; pass `include_formatting=False` to flatten emphasis. |
| `json` | All extraction helpers | Machine-readable text and metadata. | `with_metadata=False` returns at least `text` and `comments`; `with_metadata=True` adds metadata fields. | Formatting is ignored; categories/tags are semicolon-joined strings; metadata URL appears as `source`, sitename as `source-hostname`, description as `excerpt`. |
| `html` | All extraction helpers | HTML serialization of the extracted content. | `with_metadata=True` includes metadata in the serialized output. | Use when downstream expects HTML, not original markup. |
| `csv` | All extraction helpers | Tabular export of one extracted record. | Useful mainly in batch contexts; route CLI/file CSV production elsewhere. | Combining structural options with plain formats can flatten unsupported elements. |
| `xml` | All extraction helpers | Structured output preserving main/comments sections and metadata attributes. | Metadata becomes attributes when available. | Links are represented as XML refs when `include_links=True`; images as graphics when `include_images=True`. |
| `xmltei` | All extraction helpers | TEI-style XML serialization. | Metadata is enabled internally for TEI output. | `tei_validation=True` only matters for `output_format="xmltei"`; validation is diagnostic and does not replace corpus-quality review. |
| `python` | `bare_extraction()` only | Direct Python/LXML object work. | Metadata is present only if `with_metadata=True`, `only_with_metadata=True`, or blacklist/TEI-related options require it. | `extract(..., output_format="python")` and `extract_with_metadata(..., output_format="python")` are invalid. |

## Extraction options

### Content inclusion flags

- `include_comments=True` includes detected comment sections after the main text. Disable it for article-only outputs or when comments are noisy.
- `include_tables=True` includes table content. Disable it when navigation tables, product grids, or layout tables pollute the result.
- `include_links=True` keeps link targets where the chosen output format can represent them. Pass `url=` so relative links can become absolute.
- `include_images=True` tracks image targets and alt/title information in formats that support them; image extraction is experimental.
- `include_formatting=None` lets Trafilatura choose defaults. Markdown implies formatting; JSON ignores formatting; TXT with formatting can contain Markdown-like markers.

### Precision, recall, and speed

- Default balanced mode tries Trafilatura's main extraction sequence with fallbacks.
- `fast=True` skips slower fallback algorithms. It is useful for large batches or clean article pages, but it can reduce recall.
- `no_fallback=True` is deprecated; use `fast=True`.
- `favor_precision=True` keeps fewer but more central elements. Use it when boilerplate/noise leaks into output.
- `favor_recall=True` accepts more uncertain content. Use it when the article is incomplete or `None` because extraction was too strict.
- If both precision and recall are requested through `Extractor`, recall takes precedence and Trafilatura logs a warning.

### Metadata, dates, and filters

- `with_metadata=True` extracts metadata and includes it in serialized outputs where possible.
- `only_with_metadata=True` discards documents missing essential metadata: date, title, or URL.
- `url=` is useful even when content is already downloaded: it improves URL metadata, hostname, date extraction from URL patterns, and relative-link handling.
- `date_extraction_params` is passed through to `htmldate`; common keys include `extensive_search`, `original_date`, `outputformat`, and `max_date`.
- `author_blacklist={...}` can drop or reject unwanted author values.
- `url_blacklist={...}` rejects documents whose extracted URL is blacklisted.
- `record_id=` is added to non-TXT serialized metadata and contributes to generated XML/TEI/JSON-style records.

### Language filtering

- `target_language="en"` uses ISO 639-1 two-letter codes.
- Robust body-language identification requires the optional language component distributed through extras such as `trafilatura[all]`.
- Without the optional detector, Trafilatura can still use available HTML language metadata in some paths, but absence of the detector should be treated as a weaker language filter.
- A mismatched language filter yields `None` from `extract()`/`bare_extraction()`/`extract_with_metadata()`.

### Tree pruning and size limits

- `prune_xpath` accepts a string XPath or a list of XPath expressions. Matching nodes are removed before extraction and are under caller control.

```python
text = extract(html, prune_xpath=["//aside", "//div[contains(@class, 'ad')]"])
```

- The direct `max_tree_size=` parameter is deprecated in 2.2.0 and can raise `ValueError` when set. Prefer a configuration object or settings file with `MAX_TREE_SIZE`.

```python
from copy import deepcopy
from trafilatura import extract
from trafilatura.settings import DEFAULT_CONFIG

config = deepcopy(DEFAULT_CONFIG)
config["DEFAULT"]["MAX_TREE_SIZE"] = "5000"
text = extract(html, config=config)
```

### Config files and `settingsfile`

- `config=` accepts a `ConfigParser`, commonly a copy of `DEFAULT_CONFIG`.
- `settingsfile="my-settings.cfg"` loads a settings file and merges it with defaults.
- Useful extraction settings include `MIN_EXTRACTED_SIZE`, `MIN_OUTPUT_SIZE`, `MIN_EXTRACTED_COMM_SIZE`, `MIN_OUTPUT_COMM_SIZE`, `MAX_TREE_SIZE`, and `EXTENSIVE_DATE_SEARCH`.

## `Extractor` settings object

Use `Extractor` when the same option bundle should be reused across many calls.

```python
from trafilatura import extract
from trafilatura.settings import Extractor

options = Extractor(
    output_format="json",
    fast=True,
    comments=False,
    tables=False,
    links=True,
    url="https://example.org/article",
    with_metadata=True,
)
json_text = extract(html, options=options)
```

Constructor keywords:

| Keyword | Meaning |
| --- | --- |
| `output_format` | One of `csv`, `html`, `json`, `markdown`, `txt`, `xml`, `xmltei`, or `python` for `bare_extraction()`. |
| `fast` | Skip fallback algorithms. |
| `precision`, `recall` | Select focus; recall overrides precision if both are true. |
| `comments`, `tables`, `formatting`, `links`, `images` | Same inclusion controls as function flags. |
| `dedup` | Enable duplicate segment/document filtering. |
| `lang` | Target language code. |
| `url`, `source` | Source metadata and relative-link base. |
| `with_metadata`, `only_with_metadata`, `tei_validation` | Metadata and TEI behavior. |
| `author_blacklist`, `url_blacklist` | Rejection/cleanup filters. |
| `date_params` | Dict passed to date extraction. |
| `config` | `ConfigParser` carrying size, timeout, and extraction thresholds. |

## Expected `None` or empty outputs

`extract()`, `bare_extraction()`, and `extract_with_metadata()` can return `None` when Trafilatura intentionally discards input. Common reasons:

- Empty, invalid, non-HTML, or too-fragmentary input.
- Text and comments are below configured minimum output sizes.
- `only_with_metadata=True` but title/date/URL are missing.
- `target_language` rejects the document.
- URL or author blacklist rejects metadata.
- Deduplication rejects the document.
- A config-driven `MAX_TREE_SIZE` rejects an oversized output tree.

`html2txt()` and `baseline()` usually return empty strings/zero lengths rather than `None`.
