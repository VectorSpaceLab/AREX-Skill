# Trafilatura CLI Reference

Trafilatura exposes the console script `trafilatura`, mapped to `trafilatura.cli:main`. Use `python -m trafilatura.cli` as a reliable fallback when the package is installed in the active Python interpreter but the console script is not on `PATH`.

```bash
trafilatura --help
trafilatura --version
python -m trafilatura.cli --help
```

## Command shape

```text
trafilatura [-h] [-i INPUT_FILE | --input-dir INPUT_DIR | -u URL]
            [--parallel PARALLEL] [-b BLACKLIST] [--list]
            [-o OUTPUT_DIR] [--backup-dir BACKUP_DIR] [--keep-dirs]
            [--feed [FEED] | --sitemap [SITEMAP] | --crawl [CRAWL] |
             --explore [EXPLORE] | --probe [PROBE]] [--archived]
            [--url-filter URL_FILTER [URL_FILTER ...]] [-f]
            [--formatting] [--links] [--images] [--no-comments]
            [--no-tables] [--only-with-metadata] [--with-metadata]
            [--target-language TARGET_LANGUAGE] [--deduplicate]
            [--config-file CONFIG_FILE] [--precision] [--recall]
            [--output-format {csv,json,html,markdown,txt,xml,xmltei} |
             --csv | --html | --json | --markdown | --xml | --xmltei]
            [--validate-tei] [-v] [--version]
```

The parser enforces one primary input mode, one navigation mode, and one output-format selector. It does not prevent every cross-group mismatch, so still check `--keep-dirs`, `--list`, and format/validation interactions below.

## Flag groups

### Input

| Flag | Use | Notes |
|---|---|---|
| no input flag | Read bytes from stdin | Pipe or redirect an HTML response/body. If invoked interactively with no stdin, the command waits for input. |
| `-u URL`, `--URL URL` | Download and extract one URL | Quote URLs. Use for a single live page, not a file containing URLs. |
| `-i INPUT_FILE`, `--input-file INPUT_FILE` | Batch URL list | UTF-8 text file. One URL per line is expected; only valid URL lines are retained, duplicates are removed while preserving order. Can combine with navigation flags such as `--feed --list`. |
| `--input-dir INPUT_DIR` | Walk local files | Processes downloaded HTML files from a directory tree. Prefer a relative directory when pairing with `--keep-dirs`. |
| `--parallel N` | Worker count | Used for URL downloads/discovery and local file processing. Default is up to 16 cores. Start with `1` for reproducibility and network politeness. |
| `-b FILE`, `--blacklist FILE` | URL blacklist | Lines are normalized and used to discard unwanted URLs during URL-store creation. |

### Output

| Flag | Use | Notes |
|---|---|---|
| no `-o` | Print result to stdout | Best for single stdin or single URL. Batch stdout can be unordered/interleaved with parallel workers. |
| `-o DIR`, `--output-dir DIR` | Write extracted results | Directory is created when possible and must be writable. |
| `--backup-dir DIR` | Preserve raw downloaded HTML | Applies to URL downloads; writes gzip-compressed `.html.gz` source backups when gzip support is available. |
| `--keep-dirs` | Mirror local input paths | Requires `-o/--output-dir`. Intended for `--input-dir`; it keeps directory structure and base file names, then changes the extension to the selected output extension. |
| `--list` | Print URLs only | No downloading or extraction. Extraction/format/backup flags are ignored and may trigger a warning. |

### Navigation invocation

These flags are useful from the CLI, but detailed feed/sitemap/crawl mechanics belong to `discovery-downloads`.

| Flag | Use |
|---|---|
| `--feed [FEED]` | Find feeds from a homepage or process a known feed URL. Use `--list` to print URLs. |
| `--sitemap [SITEMAP]` | Discover URLs from a site or known sitemap URL. Use `--list` to inspect before extraction. |
| `--crawl [URL]` | Crawl a fixed number of internal pages and print found links. |
| `--explore [URL]` | Combine sitemap discovery and crawling. |
| `--probe [URL]` | Print URLs whose pages appear extractable; works best with `--target-language`. |
| `--archived` | For failed URL downloads, try Internet Archive fallback URLs. |
| `--url-filter PATTERN [PATTERN ...]` | Keep only URLs containing one of the supplied string patterns. |

### Extraction options

| Flag | Effect | Interactions |
|---|---|---|
| `-f`, `--fast` | Skip fallback extraction paths | Faster but may return less content. |
| `--precision` | Favor cleaner central content | If both precision and recall are set, recall wins in the extractor settings. |
| `--recall` | Favor including more candidate content | Try when expected content is missing. |
| `--formatting` | Preserve inline formatting tags where format supports it | Markdown implies formatting by default. Has no effect for JSON output. |
| `--links` | Include links and targets where supported | Most useful with Markdown/XML-like outputs. |
| `--images` | Include image sources/attributes where supported | Most useful with XML/XML-TEI. |
| `--no-comments` | Drop comments | Comments are included by default. |
| `--no-tables` | Drop tables | Tables are included by default. |
| `--with-metadata` | Add extracted metadata to output | Metadata fields depend on the HTML and selected output format. |
| `--only-with-metadata` | Output only documents with title, URL, and date | Common cause of empty output on local files or sparse pages. |
| `--target-language CODE` | Filter output by ISO 639-1 language | Requires the optional language detection dependency from `trafilatura[all]`. Without it, behavior is limited by installed components. |
| `--deduplicate` | Filter duplicate documents/sections | Use for repeated pages/sections; conceptual deduplication details belong to `corpus-quality`. |
| `--config-file FILE` | Override settings | Use a `[DEFAULT]` config. A complete baseline config is safest for reproducible batch work. |

### Format options

Choose one selector:

| Selector | Output format | File extension with `-o` |
|---|---|---|
| default or `--output-format txt` | Plain text | `.txt` |
| `--markdown` or `--output-format markdown` | Markdown | `.txt` in CLI file output |
| `--html` or `--output-format html` | HTML | `.txt` in CLI file output |
| `--csv` or `--output-format csv` | CSV | `.csv` |
| `--json` or `--output-format json` | JSON | `.json` |
| `--xml` or `--output-format xml` | XML | `.xml` |
| `--xmltei` or `--output-format xmltei` | XML-TEI | `.xml` |
| `--validate-tei` | Validate XML-TEI output | Effective only when the selected output format is `xmltei`. |

## Output naming rules

- Without `-o`, the extracted result is written to stdout with a trailing newline.
- With `-o`, output directories are created as needed.
- Without `--keep-dirs`, filenames are generated from content hashes or from backup slugs; large batches are split into numbered subdirectories after the package's per-directory limit.
- With `--backup-dir` on URL downloads, the raw HTML backup receives a random slug and the extracted output reuses that slug, making backup/result pairs easier to match.
- With `--keep-dirs`, the output path mirrors the original local file path under `-o` and strips the original extension before appending the selected output extension.

## Quick recipes

```bash
# Stdin, Markdown with metadata
cat page.html | trafilatura --markdown --with-metadata > page.md

# Single URL, JSON to stdout
trafilatura -u 'https://example.org/article' --json --with-metadata

# URL list to XML files, keeping raw downloaded HTML backups
trafilatura -i urls.txt -o extracted-xml --backup-dir raw-html --xml --parallel 2

# Local directory to XML-TEI, mirrored paths, validation enabled
trafilatura --input-dir html-pages -o tei-pages --keep-dirs --xmltei --validate-tei --parallel 1

# Discovery/list-only: inspect sitemap URLs before extracting
trafilatura --sitemap 'https://example.org/' --list > urls.txt
```

## Exit status and stderr signals

- `0`: no URL download errors, parser/help/version success, or list-only success.
- `1`: some URL downloads failed but not nearly all.
- `126`: more than 99% of URL downloads failed; treat the batch as effectively unavailable or blocked.
- `ERROR: file size`: stdin/local input violates configured min/max input size.
- `ERROR: empty document`: no input bytes were available for extraction.
- `--list only prints URLs; these options are ignored: ...`: list-only mode received extraction or output-format options that do not apply.

## Safe command construction

Shell examples must quote untrusted paths and URLs:

```bash
url='https://example.org/article?x=1&y=2'
trafilatura -u "$url" --markdown --with-metadata
```

Python automation should avoid `shell=True`:

```python
import subprocess

cmd = [
    "trafilatura",
    "--input-dir", "html-pages",
    "-o", "txt-pages",
    "--keep-dirs",
    "--markdown",
    "--parallel", "1",
]
completed = subprocess.run(cmd, check=True, text=True, capture_output=True)
```

For stdin input in Python:

```python
import subprocess

html = b"<html><body><article><h1>Title</h1><p>Enough article text...</p></article></body></html>"
completed = subprocess.run(
    ["trafilatura", "--markdown", "--with-metadata"],
    input=html,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check=True,
)
print(completed.stdout.decode("utf-8"))
```
