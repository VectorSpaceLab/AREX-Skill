# Deduplication

Trafilatura has two distinct deduplication layers that solve different corpus problems:

1. **Exact repeated segment/document filtering** during extraction with `deduplicate=True`, `Extractor(dedup=True)`, and `duplicate_test()`.
2. **Document-level near-duplicate detection** after extraction with `Simhash` and `content_fingerprint()`.

Use exact filtering for repeated boilerplate and duplicate pages inside the same extraction process. Use Simhash/fingerprints to cluster or reject near-identical documents across a corpus manifest.

## Exact extraction deduplication

### High-level API

```python
from trafilatura import extract

text = extract(
    html,
    url="https://example.org/article",
    output_format="txt",
    include_comments=False,
    deduplicate=True,
)
```

Equivalent configuration object:

```python
from trafilatura import extract
from trafilatura.settings import Extractor

options = Extractor(output_format="txt", comments=False, dedup=True, url="https://example.org/article")
text = extract(html, options=options)
```

Effects:

- Repeated extracted text segments can be removed while the extraction tree is processed.
- A document body can be discarded as a duplicate, causing `extract()` to return `None`.
- The cache is process-local; separate worker processes do not share a central duplicate memory.
- Defaults are intentionally conservative: very short segments are ignored and several repetitions can be allowed before a segment is considered duplicate.

### Tuning exact duplicate detection

The relevant `Extractor` attributes are loaded from Trafilatura settings:

| Attribute | Meaning |
| --- | --- |
| `dedup` | Turns exact duplicate testing on/off. |
| `min_duplcheck_size` | Minimum segment length before a text span is considered for duplicate testing. |
| `max_repetitions` | Number of repeated observations tolerated before `duplicate_test()` returns `True`. |

For a strict one-off check of short elements:

```python
from lxml.etree import fromstring
from trafilatura.deduplication import duplicate_test
from trafilatura.settings import Extractor

options = Extractor()
options.min_duplcheck_size = 0
options.max_repetitions = 0

element = fromstring("<p>Repeated footer text.</p>")
assert duplicate_test(element, options) is False   # first observation
assert duplicate_test(element, options) is True    # repeated observation
```

For normal corpus extraction, prefer `deduplicate=True` or `Extractor(dedup=True)` instead of calling `duplicate_test()` directly. Direct calls are best for validation, custom tree processing, or debugging a suspected boilerplate span.

### Cache hygiene

When running multiple independent experiments in the same Python process, clear Trafilatura caches between experiments so earlier pages do not affect later assertions:

```python
from trafilatura.meta import reset_caches

reset_caches()
```

This is especially important for tests that intentionally repeat the same HTML and expect the first run to be accepted.

## Near-duplicate and fingerprint workflow

Exact deduplication does not tell you whether two different pages are nearly the same article. Use Simhash for document-level similarity.

```python
from trafilatura.deduplication import Simhash, content_fingerprint

first = "The minister announced a new policy today. The full report follows."
second = "The minister announced the new policy today. The full report follows."
third = "A sports team won after a late goal."

h1 = Simhash(first)
h2 = Simhash(second)
h3 = Simhash(third)

assert h1.similarity(h2) > 0.80
assert h1.similarity(h3) < h1.similarity(h2)

hex_key = content_fingerprint(first)  # hexadecimal simhash string
```

`Simhash(existing_hash=...)` can rebuild a hash object from a stored integer or hex string:

```python
stored = h1.to_hex()
restored = Simhash(existing_hash=stored)
assert restored.similarity(h1) == 1.0
```

### Choosing a threshold

There is no universal threshold. Use a labeled sample from the target corpus:

- Start with `similarity >= 0.95` for almost-identical duplicates.
- Try `0.90` for syndicated articles with minor edits.
- Go lower only when false merges are cheap and manual review is available.
- Always inspect several false-positive and false-negative pairs before applying a threshold to the whole corpus.

A manifest-oriented workflow:

```python
from trafilatura import extract
from trafilatura.deduplication import Simhash, content_fingerprint

seen = []  # list of (record_id, Simhash)
records = []

for record_id, url, html in input_pages:
    text = extract(html, url=url, output_format="txt", include_comments=False, deduplicate=True)
    if not text:
        continue
    current = Simhash(text)
    nearest = max((current.similarity(prev) for _, prev in seen), default=0.0)
    records.append({
        "id": record_id,
        "url": url,
        "fingerprint": content_fingerprint(text),
        "nearest_similarity": nearest,
        "near_duplicate": nearest >= 0.95,
        "text": text,
    })
    if nearest < 0.95:
        seen.append((record_id, current))
```

This keeps the audit trail: exact extraction deduplication may drop repeated sections or whole duplicate bodies, while the Simhash threshold labels near-duplicate documents without silently deleting them.

## Hash filenames

Trafilatura's CLI utilities include a content-derived filename helper:

```python
from trafilatura.cli_utils import generate_hash_filename

filename_stem = generate_hash_filename(extracted_text_or_xml)
```

Properties:

- XML/HTML-like tags are stripped before hashing for filename purposes.
- The output is URL-safe base64 text suitable as a filename stem.
- Identical content receives the same stem; nearly identical content is likely to be similar at the bag-of-words hash level but should not be treated as a collision-proof identity guarantee.

Use hash filenames for storage paths, not as the only corpus id. Keep a manifest with URL, record id, output path, and `content_fingerprint()`.

## Exact versus near-duplicate decision table

| Symptom | Use | Rationale |
| --- | --- | --- |
| Same footer/nav/cookie text repeats on many pages | `deduplicate=True`; tune `min_duplcheck_size` and `max_repetitions` only if needed | Segment-level exact cache catches repeated boilerplate that escaped normal cleaning. |
| Same URL downloaded twice in one worker | `deduplicate=True` plus manifest URL de-duplication | Extraction may return `None` for duplicate body; URL manifest prevents wasted work. |
| Syndicated articles differ by timestamp, ads, or small wording edits | `Simhash.similarity()` over extracted plain text | Exact cache will miss near duplicates. |
| Need stable content key for downstream joins | `content_fingerprint(text)` plus source URL/record id | Fingerprint is compact and deterministic, but keep provenance identifiers. |
| Need output file names not dependent on crawl order | `generate_hash_filename(result)` | Stable filename stem; still store a manifest. |

## Validation steps

Run the bundled no-network smoke after installing Trafilatura:

```bash
python scripts/corpus_quality_smoke.py
```

For your own corpus, add three assertions to a small sample before scaling:

1. A page with repeated boilerplate either loses that boilerplate or is marked for manual cleanup.
2. Two known duplicate pages have equal or very high Simhash similarity.
3. Two unrelated pages stay below your chosen near-duplicate threshold.
