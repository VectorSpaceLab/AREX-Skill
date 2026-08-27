# Data Formats And Corpus Quality

Trafilatura can emit corpus material as plain text, Markdown, HTML, XML, XML-TEI, JSON, CSV/TSV, or Python `Document` objects. At corpus scale, pick the format from the downstream contract first, then decide metadata strictness and validation gates.

## Format selection

| Downstream use | Prefer | Why | Main checks |
| --- | --- | --- | --- |
| Simple NLP, concordances, token counts, search indexes | `output_format="txt"` | Small, readable, one text per record; comments can be appended when enabled. | Non-empty text, language/length gates, duplicate filtering. |
| Same as TXT but with headings, lists, links, emphasis, code, tables, or images represented for humans/LLM prompts | `output_format="markdown"` | Markdown defaults to formatted output; explicit `include_formatting=False` strips formatting. | Markdown-safe delimiters, table/link/image settings, metadata YAML if enabled. |
| Structured extraction tree without TEI header obligations | `output_format="xml"` | Preserves `main` and `comments` branches plus metadata attributes on the `<doc>` root. | XML parses cleanly; metadata attributes present when available. |
| Corpus-linguistics interchange, TXM/Voyant/XML-TEI workflows, archival structure | `output_format="xmltei"` | Emits a TEI document with `teiHeader`, body `div type="entry"`, and comments `div type="comments"`. | XML parses and `trafilatura.xml.validate_tei()` returns `True`. |
| Data frames, document stores, downstream analytics | `output_format="json"` | One JSON object string per document; good for JSONL when one record is written per line/file. | `json.loads()`, stable field list, Unicode preserved. |
| Spreadsheet or simple tabular import | `output_format="csv"` | A tab-delimited single row per extracted document, using `null` for missing fields. | Parse with tab delimiter; verify field order and null handling. |
| Programmatic inspection before custom serialization | `bare_extraction(..., output_format="python")` | Returns a `Document` object with body/comment lxml trees and metadata attributes. | Check attributes before serialization; serialize yourself only when needed. |

## Extraction knobs that affect corpus quality

```python
from trafilatura import extract

result = extract(
    html,
    url="https://example.org/article-1",   # helps metadata/source fields
    record_id="doc-000001",                # stable corpus id when available
    output_format="xmltei",                # txt, markdown, xml, xmltei, json, csv, html
    with_metadata=True,                     # include metadata in serial outputs
    include_comments=False,                 # corpus policy: comments as content or not
    include_tables=True,                    # preserve table text/structure
    include_links=False,                    # set True only if link targets matter
    include_images=False,                   # set True only if image placeholders matter
    deduplicate=True,                       # exact repeated segment/document filtering
    tei_validation=True,                    # useful only for output_format="xmltei"
)
```

Notes:

- `with_metadata=True` enriches outputs, but it does not guarantee every field exists on every page.
- `only_with_metadata=True` is a strict filter: documents missing essential metadata (`date`, `title`, or `url`) are discarded and `extract()` returns `None`.
- `output_format="xmltei"` forces metadata extraction internally because the TEI header needs metadata-like fields. Missing values are still possible and may be filled with neutral placeholders where TEI conformance requires a node.
- `include_formatting` is ignored for JSON text; Markdown defaults to formatted output unless explicitly disabled.
- `include_comments=False` is often the safest corpus default when comment threads are not part of the target corpus.

## Metadata fields and serialized shape

The internal `Document` carries these commonly useful metadata fields:

- `title`, `author`, `date`, `url`, `hostname`, `sitename`, `description`
- `categories`, `tags`, `license`, `id`, `fingerprint`, `language`
- `image`, `pagetype`, `filedate`
- body/comment fields: `body`, `commentsbody`, `text`, `comments`, `raw_text`

### JSON

With `with_metadata=True`, JSON contains document slots plus normalized aliases:

- `url` becomes `source`
- `sitename` becomes `source-hostname`
- `description` becomes `excerpt`
- `categories` and `tags` are semicolon-joined strings
- `body` becomes plain `text`
- `commentsbody` becomes plain `comments`

Without metadata, JSON contains at least `text` and `comments`.

Validation snippet:

```python
import json
from trafilatura import extract

payload = extract(html, output_format="json", with_metadata=True)
assert payload is not None
record = json.loads(payload)
assert isinstance(record.get("text"), str) and record["text"].strip()
# Metadata can be absent; require it only if your corpus policy says so.
for optional in ("title", "author", "date", "fingerprint", "source"):
    record.get(optional)
```

### CSV/TSV

Trafilatura's `csv` output is a tab-delimited row with this order:

1. `url`
2. `id`
3. `fingerprint`
4. `hostname`
5. `title`
6. `image`
7. `date`
8. extracted main `text`
9. extracted `comments`
10. `license`
11. `pagetype`

Missing values are rendered as `null`. Validate with Python's CSV reader using `delimiter="\t"`:

```python
import csv
from io import StringIO
from trafilatura import extract

row_text = extract(html, url=url, record_id="doc-1", output_format="csv", with_metadata=True)
assert row_text is not None
row = next(csv.reader(StringIO(row_text), delimiter="\t"))
assert len(row) == 11
url_value, record_id, fingerprint, hostname, title, image, date, text, comments, license_, pagetype = row
assert text != "null" and text.strip()
```

### XML

`output_format="xml"` returns a `<doc>` root. Available metadata is represented as attributes (`title`, `author`, `date`, `url`, `hostname`, `sitename`, `description`, `categories`, `tags`, `license`, `id`, `fingerprint`, `language`). The body branches are:

- `<main>` for the extracted main text tree
- `<comments>` for extracted comments when present/enabled

Validation snippet:

```python
from lxml import etree
from trafilatura import extract

xml_text = extract(html, output_format="xml", with_metadata=True)
assert xml_text is not None
root = etree.fromstring(xml_text.encode("utf-8"))
assert root.tag == "doc"
assert root.find("main") is not None
```

### XML-TEI

`output_format="xmltei"` builds a TEI document with:

- `<teiHeader>` containing title, author when available, publication/source notes, fingerprint note, profile/classification fields, and Trafilatura application metadata.
- `<text><body><div type="entry">...` for the main text.
- `<div type="comments">...` for comments.
- Heading-like elements converted to TEI-compatible `<ab type="header" rend="hN">` where appropriate.

Validation snippet:

```python
from lxml import etree
from trafilatura import extract
from trafilatura.xml import validate_tei

tei = extract(
    html,
    url=url,
    record_id="doc-1",
    output_format="xmltei",
    with_metadata=True,
    tei_validation=True,
)
assert tei is not None
tree = etree.fromstring(tei.encode("utf-8"))
assert tree.tag.endswith("TEI")
assert validate_tei(tree) is True
```

`tei_validation=True` logs validation status during extraction; it does not replace explicit validation in a corpus acceptance script.

## Corpus-level ID and fingerprint policy

Use more than one identifier:

- **Source URL**: keep the original URL whenever possible.
- **Stable record id**: pass `record_id=` when the corpus has its own id space.
- **Trafilatura fingerprint**: with metadata enabled, Trafilatura computes a content fingerprint from the title and raw text when enough information is available.
- **Custom content fingerprint**: use `trafilatura.deduplication.content_fingerprint(text)` when you need a separate cross-run near-duplicate key.
- **Hash filename**: use hash-based names when file paths should be derived from content rather than URL order. See [deduplication.md](deduplication.md) for `generate_hash_filename()`.

## Quality acceptance checklist for a corpus batch

For each batch or representative sample:

1. Count input pages, `None` results, empty outputs, and outputs dropped by `only_with_metadata=True`.
2. Validate the serialization: `json.loads()`, tab-delimited row length, `lxml.etree.fromstring()`, and `validate_tei()` for XML-TEI.
3. Check metadata coverage rates separately from extraction success: title/date/author/source/fingerprint should not be treated as guaranteed.
4. Decide whether comments belong to the corpus; if not, set `include_comments=False` consistently before benchmarking or deduplication.
5. Track exact duplicate drops (`deduplicate=True`) separately from near-duplicate clusters (`Simhash` thresholds) so users can audit data loss.
6. Preserve one raw-source pointer or provenance field per record, but do not make downstream quality checks depend on reopening the original source checkout.
