---
name: trafilatura
description: "Use Trafilatura for web text discovery, downloading, extraction,
  metadata, CLI batch processing, deduplication, and structured corpus outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Trafilatura Repo Skill

Use this skill when a task involves Trafilatura, or when the task is about extracting clean text and metadata from HTML, preparing web-corpus data, discovering article URLs from feeds/sitemaps/crawls, or using a Python/CLI web-scraping tool that outputs TXT, Markdown, JSON, CSV, HTML, XML, or XML-TEI.

Trafilatura is both a Python package and a command-line tool. It can fetch or accept HTML, isolate main text and metadata, preserve selected structure, process batches, deduplicate repeated text, and produce corpus-friendly outputs.

## Before you start

1. Install or verify the package:
   ```bash
   python -m pip install trafilatura
   python - <<'PY'
   import trafilatura
   print(trafilatura.__version__)
   print(trafilatura.extract('<html><body><p>Hello from Trafilatura.</p></body></html>'))
   PY
   ```
2. If optional features are requested, install the relevant extra instead of assuming it is present:
   - `trafilatura[all]` for language detection, faster encoding/compression/date handling, SOCKS proxy support, and `pycurl`-based download fallback.
   - `trafilatura[eval]` only for benchmark/evaluation comparisons; it is not needed for normal extraction.
3. Run [scripts/check_trafilatura_environment.py](scripts/check_trafilatura_environment.py) for a no-network import, CLI, extraction, metadata, and deduplication smoke check.
4. Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill matches a current checkout or before refreshing the skill.
5. Read [references/package-overview.md](references/package-overview.md) for the shared capability map, output formats, install extras, and common constraints.
6. Use [references/troubleshooting.md](references/troubleshooting.md) for install/import, CLI PATH, optional-extra, config, network, and routing failures that cross sub-skill boundaries.

## Route by task

| User task or signal | Read |
| --- | --- |
| In-memory Python extraction from HTML strings, bytes, `Response` objects, or LXML trees | [sub-skills/python-extraction/SKILL.md](sub-skills/python-extraction/SKILL.md) |
| Choose `extract()`, `bare_extraction()`, `extract_metadata()`, `html2txt()`, `baseline()`, output formats, metadata, comments, tables, links, images, or `Extractor` options | [sub-skills/python-extraction/SKILL.md](sub-skills/python-extraction/SKILL.md) |
| Use the `trafilatura` command, stdin, `-u/--URL`, URL lists, local directories, output directories, backups, `--keep-dirs`, `--parallel`, or `--config-file` | [sub-skills/cli-batch-processing/SKILL.md](sub-skills/cli-batch-processing/SKILL.md) |
| Build shell commands for TXT/Markdown/JSON/HTML/XML/XML-TEI output or CLI metadata/dedup/precision/recall flags | [sub-skills/cli-batch-processing/SKILL.md](sub-skills/cli-batch-processing/SKILL.md) |
| Download pages with `fetch_url()`/`fetch_response()`, inspect `Response`, manage polite URL queues, or troubleshoot SSL/proxy/timeouts | [sub-skills/discovery-downloads/SKILL.md](sub-skills/discovery-downloads/SKILL.md) |
| Discover URLs from feeds, sitemaps, focused crawling, `--feed`, `--sitemap`, `--crawl`, `--explore`, `--probe`, `--archived`, `--url-filter`, or `--list` | [sub-skills/discovery-downloads/SKILL.md](sub-skills/discovery-downloads/SKILL.md) |
| Build a corpus, choose JSON/CSV/XML/XML-TEI, validate TEI/XML, deduplicate boilerplate, compute Simhash/fingerprints, or understand evaluation benchmarks | [sub-skills/corpus-quality/SKILL.md](sub-skills/corpus-quality/SKILL.md) |

## Common decisions

- Use Python APIs when the workflow already has HTML in memory or needs downstream parsing and programmatic error handling.
- Use the CLI when the workflow is a shell pipeline, local HTML directory conversion, URL-list batch, or reproducible command recipe.
- Use discovery/download guidance before extraction when URLs must be found, filtered, throttled, or fetched politely.
- Use corpus-quality guidance when many pages must be validated, deduplicated, fingerprinted, or converted into analysis-friendly structured outputs.
- Treat live network access, large crawls, benchmark corpora, credentials, and optional extras as explicit runtime decisions. The bundled scripts are no-network checks.

## Minimal Python extraction

```python
from trafilatura import extract

html = """<html><body><article><h1>Title</h1><p>Main article text with enough content.</p></article></body></html>"""
text = extract(html, output_format="txt", include_comments=False)
if text is None:
    # See python-extraction troubleshooting for size thresholds, recall mode, and fallbacks.
    raise RuntimeError("Trafilatura found no usable main text")
```

## Minimal CLI extraction

```bash
trafilatura --help
cat page.html | trafilatura --markdown --with-metadata --no-comments
trafilatura --input-dir html-pages --output-dir extracted --json --parallel 2
```

## Scope boundaries

- Trafilatura can help discover and crawl within documented limits, but it is not a full anti-bot bypass, browser automation, authentication, JavaScript rendering, or web-scale crawler system.
- Optional language detection and some speed/download backends need optional extras; absence of those extras should be reported as a capability limit.
- Benchmark/evaluation workflows are intentionally separate from ordinary extraction because they require extra packages and larger data.
- Runtime guidance in this skill is self-contained and should not require reopening the source repository.
