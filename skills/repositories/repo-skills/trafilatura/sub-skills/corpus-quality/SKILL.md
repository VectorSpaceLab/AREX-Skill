---
name: corpus-quality
description: "Corpus-level quality, deduplication, structured output,
  validation, and evaluation guidance for Trafilatura web corpora."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Corpus Quality

Use this sub-skill when a Trafilatura task is about many-page corpus quality rather than one-page extraction mechanics: duplicate removal, stable fingerprints or file names, XML/TEI/CSV/JSON corpus outputs, metadata completeness, TEI/XML validation, benchmark context, or deciding which quality checks are safe to run.

## Route by need

| Need | Use |
| --- | --- |
| Choose a corpus output format, validate JSON/CSV/XML/XML-TEI, or reason about metadata fields | [references/data-formats-and-quality.md](references/data-formats-and-quality.md) |
| Remove repeated boilerplate, detect exact duplicate segments, compute near-duplicate fingerprints, or use Simhash | [references/deduplication.md](references/deduplication.md) |
| Decide whether to run the bundled smoke, safe native validation classes, the quality gate, or heavy benchmark comparisons | [references/benchmarks-and-evaluation.md](references/benchmarks-and-evaluation.md) |
| Diagnose duplicate boilerplate, invalid XML/TEI, missing metadata, benchmark dependency gaps, or NLTK data issues | [references/troubleshooting.md](references/troubleshooting.md) |
| Run a no-network executable check for this sub-skill's core assumptions | [scripts/corpus_quality_smoke.py](scripts/corpus_quality_smoke.py) |

## Operating boundaries

- For basic `extract()`, `bare_extraction()`, `html2txt()`, metadata extraction, or one-page API snippets, route to `python-extraction` first and return here only for corpus-quality choices.
- For command-line batching mechanics, input lists, output directories, backups, or parallel CLI operation, route to `cli-batch-processing`; this sub-skill only explains the corpus-quality consequences of those outputs.
- For live download, crawling, feeds, sitemaps, URL stores, or network throttling, route to `discovery-downloads`.
- Do not require the original repository checkout. Use the bundled references and script here; native benchmark/test labels in the references are selection guidance, not runtime dependencies.

## Fast decision checklist

1. Pick the output contract: TXT/Markdown for reading or simple NLP, JSON for flexible downstream analysis, CSV/TSV for tabular pipelines, XML for structured extraction trees, or XML-TEI for corpus-linguistics interchange and validation.
2. Decide metadata strictness: `with_metadata=True` enriches outputs; `only_with_metadata=True` drops documents missing title, date, or URL.
3. Enable exact duplicate filtering when repeated page sections or whole documents pollute a corpus: `deduplicate=True` or `Extractor(dedup=True)`.
4. Add document-level fingerprints for cross-run deduplication: `content_fingerprint()` for content identity/similarity tracking, `Simhash` for thresholded near-duplicate comparisons, and hash-based names when the output path should reflect content.
5. Validate a representative sample before scaling: parse JSON/CSV/XML outputs, call `validate_tei()` for XML-TEI, and run `scripts/corpus_quality_smoke.py` in an environment where Trafilatura is installed.
