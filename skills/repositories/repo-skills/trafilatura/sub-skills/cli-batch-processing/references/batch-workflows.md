# Batch and Local-File Workflows

This reference gives ready-to-adapt CLI workflows. All examples are no-credential and safe by default; commands that contact the network are marked as such. For full flag semantics see `cli-reference.md`.

## 0. Preflight for any batch

```bash
trafilatura --version
trafilatura --help >/dev/null
mkdir -p extracted raw-html logs
```

Start with a small local fixture before running a large batch:

```bash
python scripts/cli_fixture_runner.py
```

For network batches, begin with `--parallel 1`, verify outputs, then increase cautiously only when permitted by the target site and your own infrastructure.

## 1. Stdin or one local HTML file

Use stdin when an upstream command already has the HTML response body.

```bash
# Plain text to stdout
cat page.html | trafilatura

# Markdown with metadata, redirected to a file
cat page.html | trafilatura --markdown --with-metadata > page.md

# Same idea without cat
trafilatura --json --with-metadata < page.html > page.json
```

Validation checklist:

- stdout is non-empty;
- expected title/headline or article text appears;
- stderr does not contain `ERROR: file size` or a traceback;
- if `--only-with-metadata` was used, the HTML has enough metadata for title, URL/source, and date.

Avoid piping a URL string to stdin. Stdin mode expects HTML bytes. Use `-u/--URL` for a live URL.

## 2. Single URL extraction (network)

```bash
trafilatura -u 'https://example.org/article' --markdown --with-metadata
trafilatura --URL 'https://example.org/article' --xml --with-metadata > article.xml
```

Useful modifiers:

- `--recall` if known content is missing;
- `--precision` if the result contains too much navigation/sidebar noise;
- `--no-comments` and `--no-tables` when those elements are unwanted;
- `--target-language en` when optional language detection is installed and the batch must keep one language;
- `--archived` to try the Internet Archive for URL downloads that fail.

Be polite: Trafilatura has default sleeps between requests, but one-off `-u` commands can still hit blocked user-agent/IP/network conditions. Do not use this CLI to bypass access restrictions.

## 3. URL list extraction (network batch)

Create a UTF-8 list with one URL per line. Non-URL lines are ignored; duplicate URLs are collapsed in first-seen order.

```text
https://example.org/article-1
https://example.org/article-2
# comments or notes are ignored because they are not URLs
https://example.org/article-1
```

Run the batch into an output directory:

```bash
trafilatura -i urls.txt -o extracted-txt --markdown --with-metadata --parallel 1
```

Add backups to preserve downloaded HTML sources:

```bash
trafilatura \
  --input-file urls.txt \
  --output-dir extracted-xml \
  --backup-dir raw-html \
  --xml \
  --with-metadata \
  --parallel 2
```

Use URL filters and blacklists when a list contains unwanted routes:

```bash
# blacklist.txt contains URL fragments or full URLs to discard
trafilatura -i urls.txt --blacklist blacklist.txt --url-filter /articles/ /blog/ -o extracted --json
```

Validation checklist:

- expected number of result files exists in `-o`;
- backup files appear in `--backup-dir` for successful downloads when backup was requested;
- exit status is `0` or, if nonzero, stderr/logs identify which URLs failed;
- a spot-check of extracted files contains article text and metadata fields as expected.

Exit statuses from URL batches: `1` means some downloads failed; `126` means almost all downloads failed and the batch likely needs network, blocking, URL-list, or config review.

## 4. Local directory processing

Use `--input-dir` for previously downloaded HTML files. This is the safest high-throughput mode because extraction is separated from networking.

```bash
# Markdown output; results get generated names under extracted-md/
trafilatura --input-dir html-pages -o extracted-md --markdown --parallel 1

# Mirror directory structure and base file names
trafilatura --input-dir html-pages -o extracted-md --keep-dirs --markdown --parallel 1
```

For XML-TEI corpus preparation:

```bash
trafilatura \
  --input-dir html-pages \
  --output-dir tei-pages \
  --keep-dirs \
  --xmltei \
  --validate-tei \
  --with-metadata \
  --parallel 1
```

`--keep-dirs` requires `-o/--output-dir` and is intended for local directory processing. Prefer a relative `--input-dir` such as `html-pages`; using an absolute input path may create unnecessarily deep mirrored paths under the output directory. For Trafilatura 2.2.0, always test `--keep-dirs` on a nested sample before a large run; if no files appear or a path-duplication failure surfaces, run without `--keep-dirs` and map filenames downstream, or pre-flatten the input until the installed package is patched.

Validation checklist for directory mode:

```bash
find tei-pages -type f | head
find tei-pages -type f -name '*.xml' | wc -l
python scripts/cli_fixture_runner.py
```

If a directory batch prints to stdout instead of writing files, add `-o`. Parallel stdout from many files is not a stable archival format.

## 5. Listing/discovery before extraction

Use `--list` to collect URLs without downloading or extracting. This is useful for a two-stage workflow: discovery first, manual review/filtering second, extraction third.

```bash
# Sitemap URL discovery only
trafilatura --sitemap 'https://example.org/' --list > discovered-urls.txt

# Feed discovery only
trafilatura --feed 'https://example.org/' --list > feed-urls.txt

# A file of homepages or feed/sitemap roots processed in parallel for URL listing
trafilatura -i sources.txt --feed --list --parallel 2 > listed-urls.txt
```

Then inspect and filter the resulting list before extraction:

```bash
sort -u discovered-urls.txt > urls.txt
trafilatura -i urls.txt -o extracted --markdown --with-metadata --parallel 1
```

Important: `--list` is URL-only. It ignores extraction and format options such as `--json`, `--with-metadata`, `--backup-dir`, `--precision`, and `--recall`. Do not expect extracted files from a command containing `--list`.

## 6. Complete config file for reproducible batches

Use `--config-file` to adjust download pacing, file-size limits, extraction thresholds, deduplication thresholds, metadata date search, and CLI extraction timeout. A complete `[DEFAULT]` file is safest for reproducible production batches and older deployments.

Example `batch-settings.cfg`:

```ini
[DEFAULT]

# Download
DOWNLOAD_TIMEOUT = 30
MAX_FILE_SIZE = 20000000
MIN_FILE_SIZE = 10
SLEEP_TIME = 10.0
USER_AGENTS =
COOKIE =
MAX_REDIRECTS = 2

# Extraction
MIN_EXTRACTED_SIZE = 250
MIN_EXTRACTED_COMM_SIZE = 1
MIN_OUTPUT_SIZE = 1
MIN_OUTPUT_COMM_SIZE = 1
MAX_TREE_SIZE =

# CLI file processing only; set to 0 only when diagnosing platform signal issues
EXTRACTION_TIMEOUT = 30

# Deduplication
MIN_DUPLCHECK_SIZE = 100
MAX_REPETITIONS = 2

# Metadata/date extraction
EXTENSIVE_DATE_SEARCH = on

# Feed/sitemap URL behavior in CLI mode
EXTERNAL_URLS = off
```

Run with the config:

```bash
trafilatura -i urls.txt -o extracted --markdown --with-metadata --config-file batch-settings.cfg --parallel 1
```

Notes:

- Trafilatura 2.2.0 seeds package defaults before reading a custom file, but a complete file makes batch assumptions explicit.
- Increase `SLEEP_TIME` rather than using high `--parallel` when a site requires slower access.
- `MIN_FILE_SIZE` and `MAX_FILE_SIZE` are common levers for `ERROR: file size` on unusual inputs.
- `MIN_OUTPUT_SIZE`/`MIN_EXTRACTED_SIZE` can explain empty results from very short pages.

## 7. Safe command construction in shell scripts

```bash
#!/usr/bin/env bash
set -euo pipefail

input_file=${1:?usage: run_batch.sh urls.txt output_dir}
output_dir=${2:?usage: run_batch.sh urls.txt output_dir}

mkdir -p "$output_dir" raw-html
trafilatura \
  --input-file "$input_file" \
  --output-dir "$output_dir" \
  --backup-dir raw-html \
  --markdown \
  --with-metadata \
  --parallel 1
```

Do not concatenate user-provided URLs into unquoted shell strings. If a workflow is generated from Python, pass an argument list:

```python
import subprocess

subprocess.run(
    [
        "trafilatura",
        "--input-file", "urls.txt",
        "--output-dir", "extracted",
        "--markdown",
        "--with-metadata",
        "--parallel", "1",
    ],
    check=True,
)
```

## 8. Hard usability scenarios this sub-skill should support

### Mirrored XML-TEI corpus from local HTML

Goal: process an existing nested directory of local HTML pages into XML-TEI, mirror input paths, validate TEI, and avoid network access.

Command shape:

```bash
trafilatura --input-dir html-pages -o tei-pages --keep-dirs --xmltei --validate-tei --with-metadata --parallel 1
```

Assertions for later verification:

- `--keep-dirs` fails without `-o`, then succeeds with `-o`;
- nested input files map to nested `.xml` outputs;
- outputs contain XML-TEI roots and expected text;
- stderr has no TEI validation errors.

### URL discovery/listing without extraction

Goal: collect URLs from a sitemap/feed source while avoiding false expectations about extracted files.

Command shape:

```bash
trafilatura --sitemap 'https://example.org/' --list > urls.txt
```

Assertions for later verification:

- stdout contains URLs only;
- no extraction output directory is expected;
- adding `--json` or `--with-metadata` to a list-only command produces an ignored-options warning, not JSON extraction.
