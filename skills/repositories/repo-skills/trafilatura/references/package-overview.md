# Trafilatura package overview

This reference gives shared operating context for the Trafilatura repo skill. Use the sub-skills for detailed workflows.

## What Trafilatura does

Trafilatura gathers and converts web text. Its user-facing surfaces are:

- Python functions for extracting main text, metadata, comments, tables, links, images, and structured representations from HTML-like inputs.
- A `trafilatura` CLI for stdin, URLs, URL-list batches, local input directories, output directories, and structured output formats.
- URL discovery and retrieval helpers for feeds, sitemaps, focused crawling, response inspection, polite queues, and optional archive/proxy paths.
- Corpus-quality helpers for duplicate filtering, Simhash fingerprints, structured output validation, and evaluation context.

## Installation and optional extras

Base install:

```bash
python -m pip install trafilatura
```

Use a virtual environment for reproducibility. Verify with:

```bash
python - <<'PY'
import trafilatura
print(trafilatura.__version__)
print(trafilatura.extract('<html><body><p>Hello from Trafilatura.</p></body></html>'))
PY
trafilatura --version
trafilatura --help
```

Optional extras are not required for ordinary HTML extraction:

| Extra | Use when | Notes |
| --- | --- | --- |
| `trafilatura[all]` | The task needs language detection, faster encoding/compression/date handling, `pycurl`, SOCKS proxy support, or additional compression formats | If absent, base extraction still works; route missing optional behavior to troubleshooting. |
| `trafilatura[eval]` | The task is specifically to run benchmark/evaluation comparisons against other extractors | This can be slower and broader than normal extraction. Do not install for ordinary use. |
| Documentation or development extras | The task is maintaining docs or the repository, not using Trafilatura as a package | Not part of normal operating workflows. |

## Core Python APIs

| API | Use for | Returns |
| --- | --- | --- |
| `extract()` | Main HTML-to-text/structured extraction with options for output format, metadata, comments, tables, links, images, precision/recall, language, and config | `str` or `None` |
| `bare_extraction()` | Programmatic access to a `Document` object or dict with body, comments, and metadata before final serialization | `Document`, `dict`, or `None` |
| `extract_with_metadata()` | A convenience path returning a `Document` with metadata | `Document` or `None` |
| `extract_metadata()` | Metadata-only extraction from HTML | `Document` metadata container |
| `html2txt()` | Broad recall text dump fallback | `str` |
| `baseline()` | Simpler/faster paragraph-oriented fallback | body element, text, length |
| `fetch_url()` | Fetch a URL and return decoded HTML | `str` or `None` |
| `fetch_response()` | Fetch a URL and inspect data/status/headers/final URL | `Response` or `None` |

For full signatures, read the relevant sub-skill references.

## Output format selection

| Format | Best for | Caveats |
| --- | --- | --- |
| `txt` | Simple downstream NLP or display | Limited structure and metadata unless header options are used. |
| `markdown` | Human-readable text with headings/formatting and optional YAML-style metadata header | Selecting Markdown automatically favors formatting preservation. |
| `json` | Downstream pipelines that need fields for text, comments, metadata, links, and images | Validate with `json.loads()` before scaling. |
| `csv` | Simple tabular exports | Some structural options may force Markdown-like text internally. |
| `html` | Preserving cleaned HTML-like structure | Use for workflows that need structure more than plain text. |
| `xml` | Structured XML output for further processing | Validate parsing on representative samples. |
| `xmltei` | Corpus-linguistics TEI interchange | Use corpus-quality guidance for validation and metadata strictness. |

## Configuration surfaces

- Function arguments handle most one-off choices: output format, metadata, comments, tables, links, images, precision/recall, fast mode, target language, `deduplicate`, `prune_xpath`, and date extraction parameters.
- `Extractor(...)` packages repeated options for multiple calls.
- A complete config file can be passed through `settingsfile` or `config`; incomplete config files can fail because expected sections/values are missing.
- CLI `--config-file` maps to the same settings concept.

## Safe validation pattern

1. Start with a tiny local HTML fixture and no network.
2. Check import/version and CLI help.
3. Run the root smoke script.
4. Run the owning sub-skill smoke script if the task is API-, CLI-, discovery-, or corpus-quality-specific.
5. Only then add live URLs, batches, optional extras, or large corpora.

## Runtime boundaries

- Do not treat a failed live download as proof that extraction is broken; separate retrieval from HTML extraction.
- Do not treat `None` output as an exception by default; it often means the document failed size, language, metadata, or extraction thresholds.
- Do not run broad crawls, benchmark corpora, or optional-download backends without explicit runtime/budget choices.
- If JavaScript rendering, login, CAPTCHA, browser automation, or anti-bot bypass is required, Trafilatura alone is not the complete tool.
