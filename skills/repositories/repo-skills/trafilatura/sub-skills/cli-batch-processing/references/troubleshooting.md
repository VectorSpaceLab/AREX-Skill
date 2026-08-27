# CLI Troubleshooting

Use this file for command-line and batch/local-file failures. For Python API calls, route to `python-extraction`; for discovery/crawl mechanics, route to `discovery-downloads`; for TEI/deduplication concepts, route to `corpus-quality`.

## Symptom-to-fix matrix

| Symptom | Likely cause | Recovery |
|---|---|---|
| `trafilatura: command not found` | Console script directory is not on `PATH` or package is not installed in the active environment. | Try `python -m trafilatura.cli --help`. If that works, fix `PATH` or call the module form. If it fails, install the package in the interpreter used by the job. |
| `No module named trafilatura`, `No module named justext`, or import traceback before help prints | The active Python interpreter does not have Trafilatura or its base dependencies. | Install Trafilatura with base dependencies, then re-run `trafilatura --help` and `python scripts/cli_fixture_runner.py`. |
| Command appears to hang with no arguments | With no input flag, Trafilatura reads stdin until EOF. | Pipe/redirect HTML (`trafilatura < page.html`) or use `-u URL`, `-i urls.txt`, or `--input-dir html-pages`. |
| Piping a URL string gives empty output or `ERROR: file size` | Stdin mode expects HTML bytes, not a URL. | Use `trafilatura -u 'https://example.org/article'` for a live URL, or download first and pipe the HTML response body. |
| `ERROR: file size` | Input is below `MIN_FILE_SIZE`, above `MAX_FILE_SIZE`, empty, binary, or not an HTML document. | Verify the file/pipe contains HTML. For legitimate unusual sizes, use `--config-file` to adjust `MIN_FILE_SIZE` or `MAX_FILE_SIZE`, then re-run a small sample. |
| `ERROR: empty document` | stdin or a download produced no bytes. | Confirm the upstream command returns a response body; for URL mode, check network reachability and status; for stdin, ensure the pipe is not empty. |
| Parser error about mutually exclusive arguments | More than one primary input, navigation, or format selector was supplied. | Choose one of `-i`, `--input-dir`, `-u`, or stdin; choose one of `--feed/--sitemap/--crawl/--explore/--probe`; choose one of `--json/--xml/...` or `--output-format`. |
| `--keep-dirs requires an output directory (-o/--output-dir)` | `--keep-dirs` was used without `-o`. | Add `-o out-dir`, e.g. `trafilatura --input-dir html-pages -o extracted --keep-dirs --markdown`. |
| Destination directory cannot be created | `-o` or `--backup-dir` points to an unwritable or invalid location. | Choose a writable output path, pre-create parent directories if needed, check disk quota, and avoid system directories in automation. |
| Output file names/extensions are surprising | CLI file output maps Markdown and HTML to `.txt`; XML and XML-TEI to `.xml`; generated names are content hashes or backup slugs unless `--keep-dirs` is active. | Plan downstream glob patterns accordingly. Use `--keep-dirs` with local directories when stable source-like names are required. |
| Mirrored output path is unexpectedly deep | `--keep-dirs` mirrored an absolute or overly broad input path. | Run from a working directory and pass a relative `--input-dir`, e.g. `--input-dir html-pages`, then write to `-o extracted`. |
| `--keep-dirs` creates no files or surfaces a duplicated path failure on nested inputs | Trafilatura 2.2.0 path construction can duplicate relative directory segments for nested local files before creating all needed parents. | Verify `--keep-dirs` on a tiny nested sample before production. If it fails, run the batch without `--keep-dirs`, pre-flatten inputs, or post-map hash-named outputs until the installed package is patched. |
| Batch output printed to stdout is unordered or hard to archive | Directory processing uses parallel workers and stdout is not a stable batch artifact. | Use `-o/--output-dir` for batch results. Use `--parallel 1` for deterministic debugging. |
| `--list only prints URLs; these options are ignored: ...` | `--list` was combined with extraction/format/backup options. | Split the job: first `--list > urls.txt`, then run extraction with `-i urls.txt -o out-dir` and the format options. |
| No files are written from a command containing `--list` | Expected behavior: list-only mode does not download or extract. | Remove `--list` for extraction, or use the resulting URL list as input to a second command. |
| `--only-with-metadata` yields empty output | The document lacks required title, URL/source, or date metadata. Local files often have no URL unless source context can be inferred. | Use `--with-metadata` instead of `--only-with-metadata`, add source metadata upstream, or run without metadata gating. |
| Expected content is missing | Extraction favored central article content or fallback constraints discarded text. | Try `--recall`; remove restrictive flags such as `--formatting`, `--target-language`, or `--only-with-metadata`; inspect the HTML for script-rendered content. |
| Output contains too much boilerplate/noise | Extraction included navigation/sidebar material. | Try `--precision`, `--no-comments`, `--no-tables`, or switch to XML/Markdown to inspect structure before choosing a stricter workflow. |
| `--target-language` has no effect or filters unexpectedly | Optional language detection dependency may be absent, or the page text is too short/mixed-language. | Install the optional `trafilatura[all]` extra when language filtering is required; otherwise omit `--target-language` and filter downstream. |
| `--validate-tei` appears to do nothing | Validation only applies to XML-TEI output. | Use `--xmltei --validate-tei`, or remove `--validate-tei` for other formats. |
| XML-TEI validation or XML parsing fails downstream | HTML source, metadata, or included elements may produce unexpected TEI/XML content, or validation was not enabled during extraction. | Re-run one file with `--xmltei --validate-tei --parallel 1 -v`; disable optional elements (`--links`, `--images`, `--formatting`) while debugging; inspect the single-file stderr. |
| Config file not found or settings ignored | Wrong path, missing `[DEFAULT]` section, typo in key, or automation running from a different working directory. | Use an explicit config path. Include a `[DEFAULT]` section and the baseline keys shown in `batch-workflows.md`. Validate with `python scripts/cli_fixture_runner.py` and a one-file batch before scaling. |
| `signal`-related timeout errors in local directory processing | CLI extraction timeout uses signal-based process behavior that can vary by platform. | For diagnosis only, set `EXTRACTION_TIMEOUT = 0` in a config file and run `--parallel 1`; restore a finite timeout for production. |
| URL batch exits `1` | Some URLs failed. | Review stderr/logs and failed URLs. Retry only failed URLs after checking network status, URL correctness, throttling, and blocks. |
| URL batch exits `126` | More than 99% of URLs failed; usually wrong URL list, no network, blocked user agent/IP, DNS/TLS problem, or too-aggressive batch settings. | Stop the batch. Test one URL with `-u -v`, reduce `--parallel`, increase `SLEEP_TIME`, verify URLs, and avoid bypassing access restrictions. |
| `--backup-dir` is empty | Backups apply to URL downloads, not local `--input-dir` extraction; backup directory may be unwritable; gzip support may be unavailable. | Use `--backup-dir` with `-u` or `-i`; verify it is writable; for local HTML, the input directory already holds sources. |
| Network site blocks or returns little content | Target blocks default user agent/IP, requires cookies, or content is rendered by JavaScript/paywalled. | Do not bypass restrictions. If authorized, adjust `USER_AGENTS`, `COOKIE`, `DOWNLOAD_TIMEOUT`, and `SLEEP_TIME` in a config file; otherwise download/render content separately with permitted tooling and feed local HTML to Trafilatura. |

## Minimal diagnostic sequence

```bash
# 1. Entry point and parser
trafilatura --help >/dev/null || python -m trafilatura.cli --help

# 2. No-network fixture
python scripts/cli_fixture_runner.py

# 3. One real local file before a directory batch
trafilatura --markdown --with-metadata < page.html > page.md

# 4. One URL before a URL list batch (network)
trafilatura -u 'https://example.org/article' --markdown --with-metadata -v

# 5. Then scale cautiously
trafilatura -i urls.txt -o extracted --markdown --with-metadata --parallel 1
```

## Separating list and extraction jobs

Bad expectation:

```bash
trafilatura --sitemap 'https://example.org/' --list --json -o extracted
```

This prints URLs only and warns that `output_format` is ignored.

Correct two-step workflow:

```bash
trafilatura --sitemap 'https://example.org/' --list > urls.txt
trafilatura -i urls.txt -o extracted --json --with-metadata --parallel 1
```

## Config sanity check

Use the complete example in `batch-workflows.md` as a starting point. For batch politeness and robustness, tune these first:

- `SLEEP_TIME`: higher values reduce request pressure;
- `DOWNLOAD_TIMEOUT`: increase for slow sites;
- `MIN_FILE_SIZE`/`MAX_FILE_SIZE`: input acceptance bounds;
- `MIN_OUTPUT_SIZE`/`MIN_EXTRACTED_SIZE`: output acceptance bounds;
- `EXTRACTION_TIMEOUT`: local file processing guardrail.

After editing a config file, run one small command with `--config-file FILE --parallel 1` before launching a full list or directory batch.
