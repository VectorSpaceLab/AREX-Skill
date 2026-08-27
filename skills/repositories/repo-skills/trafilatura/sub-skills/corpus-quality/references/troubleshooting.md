# Corpus Quality Troubleshooting

## Quick triage

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Same footer, cookie banner, menu, or disclaimer appears in many extracted records | Site boilerplate escaped normal cleanup; exact dedup not enabled or thresholds too conservative. | Enable `deduplicate=True`; validate with `duplicate_test()` on the repeated element; consider `prune_xpath` for a known site template. |
| Near-identical articles both remain in the corpus | Exact dedup only catches identical segments/documents, not edited syndication copies. | Compute `Simhash` over extracted text and set a review threshold such as 0.95 after sampling. |
| Too many legitimate repeated phrases disappear | Dedup thresholds are too strict for the genre, or repeated short segments are meaningful. | Raise `min_duplcheck_size`, raise `max_repetitions`, or disable `deduplicate` and do near-duplicate review after extraction. |
| `extract(..., output_format="xmltei", tei_validation=True)` returns XML but validation later fails | The serialized TEI was modified after extraction, parsed with the wrong bytes/string handling, or contains edge-case structure. | Re-parse the exact returned string with `lxml.etree.fromstring()` and call `validate_tei()` before any downstream transformation. |
| XML parser fails before TEI validation | Output is not XML/TEI, is `None`, or was concatenated with other records without a wrapper. | Check `result is not None`; store one XML/TEI document per file or wrap multiple records in a corpus-level container you validate separately. |
| JSON/CSV output exists but metadata fields are `null`/missing | Metadata extraction is best-effort and depends on the page; `url` was not supplied; page lacks title/date/author metadata. | Pass `url=...` and `with_metadata=True`; treat fields as optional unless `only_with_metadata=True` is intended. |
| Many records become `None` after enabling `only_with_metadata=True` | Strict metadata gate is discarding pages missing title, date, or URL. | Use `with_metadata=True` without `only_with_metadata` to measure coverage first; enable strict mode only if those losses are acceptable. |
| Benchmark command reports missing packages | Full comparison needs optional packages; quality gate needs the `all` extra for parity. | Use bundled smoke for normal corpus work; install `trafilatura[all]` for the quality gate or `trafilatura[eval]` for full benchmark comparison when explicitly selected. |
| Full benchmark tries to download NLTK data repeatedly or stalls around `news-please` | NLTK tokenizer data is absent. | Download `punkt` and `punkt_tab` once before full comparison, or omit the `news-please` algorithm. |

## Duplicate boilerplate remains

Start with exact deduplication:

```python
from trafilatura import extract

text = extract(html, output_format="txt", include_comments=False, deduplicate=True)
```

If the repeated text is still present:

1. Confirm the repeated span is long enough to be considered duplicate. Default settings ignore short spans.
2. Confirm it appears repeatedly within the same Python process or worker. Exact cache state is not centralized across worker processes.
3. Check whether the text differs by timestamps, counters, whitespace, or injected link labels. If so, use Simhash or site-specific pruning instead of exact dedup.
4. For a known site template, remove the offending nodes before extraction with `prune_xpath` rather than lowering duplicate thresholds globally.

Strict duplicate probe:

```python
from lxml.etree import fromstring
from trafilatura.deduplication import duplicate_test
from trafilatura.settings import Extractor

options = Extractor()
options.min_duplcheck_size = 0
options.max_repetitions = 0

boilerplate = fromstring("<p>Subscribe to our newsletter.</p>")
assert duplicate_test(boilerplate, options) is False
assert duplicate_test(boilerplate, options) is True
```

## Near-duplicate clusters look wrong

If unrelated documents are clustered:

- Raise the similarity threshold.
- Compare only extracted main text with `include_comments=False` unless comments are part of the corpus.
- Avoid hashing extremely short texts; short documents can collide or look similar because there are too few meaningful tokens.
- Inspect the sampled tokens by checking whether boilerplate dominates the text before hashing.

If obvious duplicates are missed:

- Lower the threshold gradually (`0.95` → `0.90`) and manually inspect sample pairs.
- Normalize corpus policy first: same comment setting, same table setting, same language filter.
- Use `content_fingerprint()` as a stored key, but use `Simhash.similarity()` for thresholded comparisons.

## Invalid XML or TEI

Use separate checks for parseability and TEI conformance:

```python
from lxml import etree
from trafilatura import extract
from trafilatura.xml import validate_tei

tei = extract(html, url=url, output_format="xmltei", with_metadata=True, tei_validation=True)
assert tei is not None
root = etree.fromstring(tei.encode("utf-8"))
assert validate_tei(root) is True
```

Common pitfalls:

- Concatenating multiple TEI documents into one file without a valid wrapper.
- Modifying the XML string after extraction, especially by string replacement.
- Treating validation log warnings as fatal without checking `validate_tei()`'s boolean result.
- Expecting every metadata field to be populated; TEI can be valid with placeholder or missing optional metadata.

## Missing metadata

Metadata is extracted from HTML metadata, JSON-LD, URL context, and date heuristics. It is not guaranteed.

Recommended workflow:

```python
from trafilatura import extract
from trafilatura.metadata import extract_metadata

# Measure metadata without dropping the document.
json_record = extract(html, url=url, output_format="json", with_metadata=True)

# Inspect fields directly when debugging one page.
doc = extract_metadata(html, default_url=url)
print(doc.title, doc.author, doc.date, doc.url)
```

Actions:

- Always pass `url=` when known; it helps source and hostname fields.
- Use `record_id=` for your own stable id; do not rely on title/date being present.
- Use `only_with_metadata=True` only after measuring how many pages it will discard.
- If author/date extraction creates systematic false positives, use `author_blacklist` or `date_extraction_params` from the main extraction API.

## CSV/JSON downstream problems

CSV is tab-delimited and has no header row by default. Use the fixed field order from [data-formats-and-quality.md](data-formats-and-quality.md). Missing fields are `null`.

JSON preserves Unicode and returns a JSON object string per extracted document. If writing JSONL, write one extracted JSON string per line and do not wrap it in extra quotes.

## Benchmark extras and skip reasons

- `trafilatura[all]`: use for Trafilatura's own quality gate parity; includes speed and format-related optional dependencies.
- `trafilatura[eval]`: use for full competitor comparisons; larger and slower.
- Missing competitor libraries are skip reasons in full comparison, not necessarily failures.
- `magic-html` requires Python 3.12 or later.
- `news-please` may need NLTK `punkt` and `punkt_tab` data. Without it, it can attempt network downloads or fail per document.

For ordinary corpus building, benchmark extras are not required. Prefer the bundled smoke plus sample validation unless the user explicitly requests benchmark reproduction or package-regression evidence.
